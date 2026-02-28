"""Data Coordinator for AAP integration."""

import asyncio
from collections.abc import Mapping
from datetime import timedelta
import logging
from typing import Any, Literal, TypedDict, cast

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .arrowhead_alarm_api import ArrowheadAlarmAPI, TranslatedMessage
from .const import ZONE_NUMBER, ZONES

_LOGGER = logging.getLogger(__name__)


class ZoneStatus(TypedDict):
    """Type definition for individual zone status."""

    open: bool
    alarm: bool
    bypassed: bool


class ArrowheadData(TypedDict):
    """Type defintition for the coordinator's data."""

    partition_status: str | None
    zones: dict[int, ZoneStatus]


class ArrowheadAlarmCoordinator(DataUpdateCoordinator[ArrowheadData]):
    """Arrowhead_Alarm coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: ArrowheadAlarmAPI,
        entry_id: str,
        config_data: Mapping[str, Any],
    ) -> None:
        """Initialize coordinator."""

        self.api = api
        self.entry_id = entry_id

        self.configured_zones = config_data.get(ZONES, [])

        self._sync_in_progress = False
        self._received_zones: set[int] = set()

        scan_interval = config_data.get("scan_interval", 60)

        super().__init__(
            hass,
            _LOGGER,
            name="Arrowhead Alarm",
            update_interval=timedelta(seconds=scan_interval),
        )

        self.api.register_callback(self._async_handle_api_message)

    def _get_initial_data(self) -> ArrowheadData:
        """Return the default data structure."""
        zones_init: dict[int, ZoneStatus] = {
            int(z[ZONE_NUMBER]): ZoneStatus(open=False, alarm=False, bypassed=False)
            for z in self.configured_zones
        }
        return {
            "partition_status": "partition_disarmed",
            "zones": zones_init,
        }

    async def _async_handle_api_message(self, message: TranslatedMessage) -> None:
        """Process push messages from the API."""

        msg_type = message["type"]
        msg_data = message["data"]

        # Handle Command Responses (Success/Error)
        if msg_type == "command_response" and msg_data:
            if msg_data.get("status", None) == "error":
                _LOGGER.error(
                    "Alarm Panel returned Error Code: %s", msg_data.get("code", "")
                )
                # Optional: Fire a Home Assistant event so you can trigger a notification
                self.hass.bus.fire(
                    "arrowhead_alarm_error", {"code": msg_data.get("code", "")}
                )
            else:
                _LOGGER.debug(
                    "Alarm Panel Command Successful: %s", msg_data.get("command")
                )
            return

        if not self.data:
            self.data = self._get_initial_data()
        if not msg_data and msg_type != "sync_start":
            return

        # Create a shallow copy of the data dictionary to ensure HA sees the update
        new_data: ArrowheadData = {
            "partition_status": self.data["partition_status"],
            "zones": dict(self.data["zones"]),
        }

        # --- HANDLE SYNC START ---
        if msg_type == "sync_start":
            self._sync_in_progress = True
            self._received_zones.clear()
            return  # No need to update state yet

        if not msg_data:
            return

        # --- HANDLE ZONE UPDATES ---
        if msg_type == "zone":
            zone_id = int(msg_data.get("zone_id", 0))
            status_key: Literal["open", "alarm", "bypassed"] = cast(
                Literal["open", "alarm", "bypassed"], msg_data.get("status_type")
            )
            action: bool = msg_data.get("action", False)

            # If we are in the middle of a status dump, track this zone ID
            if self._sync_in_progress:
                self._received_zones.add(zone_id)

            # Update the zone in our data structure
            if zone_id in new_data["zones"]:
                cur_zone = cast(ZoneStatus, dict(new_data["zones"][zone_id]))
                cur_zone[status_key] = action  # type: ignore[literal-required]
                new_data["zones"][zone_id] = cur_zone

            if status_key == "alarm":
                if action:
                    _LOGGER.info(
                        "Zone %s triggered alarm. Promoting partition to in_alarm",
                        zone_id,
                    )
                    new_data["partition_status"] = "partition_in_alarm"
                else:
                    other_alarms = any(
                        z["alarm"]
                        for zid, z in new_data["zones"].items()
                        if zid != zone_id
                    )
                    if (
                        not other_alarms
                        and new_data["partition_status"] == "partition_in_alarm"
                    ):
                        _LOGGER.info(
                            "All zone alarms cleared. Restoring partition status"
                        )
                        new_data["partition_status"] = "partition_disarmed"
        # --- HANDLE PARTITION UPDATES & SYNC CLEANUP ---
        elif msg_type == "partition":
            new_status = cast(str, msg_data.get("status"))
            current_status = new_data["partition_status"]

            armed_states = [
                "partition_away_armed",
                "partition_stay_armed",
                "partition_in_alarm",
                "partition_exit_away_timing",
                "partition_exit_stay_timing",
            ]

            if current_status in armed_states and new_status in [
                "partition_ready",
                "partition_alarm_restored",
                "partition_not_ready",
                "output_on",
                "output_ready",
            ]:
                _LOGGER.debug(
                    "Shielding armed state '%s' from incoming '%s' message",
                    current_status,
                    new_status,
                )
            else:
                new_data["partition_status"] = new_status

            # Handle Sync Cleanup during a status dump
            if new_status == "partition_ready" and self._sync_in_progress:
                for zid in new_data["zones"]:
                    if zid not in self._received_zones:
                        new_data["zones"][zid] = ZoneStatus(
                            open=False, alarm=False, bypassed=False
                        )

                self._sync_in_progress = False

        # --- 4. FINALIZE ---
        # This pushes the update to all entities (binary sensors, switches, alarm panel)
        self.async_set_updated_data(new_data)

    async def _async_update_data(self) -> ArrowheadData:
        """Called periodically and during setup to connect and start listener."""

        try:
            async with asyncio.timeout(10):
                if not self.api.is_connected:
                    await self.api.connect()
                    await self.api.set_mode(2)
                await self.api.request_status()

            if self.data is None:
                return self._get_initial_data()

            return self.data  # noqa: TRY300

        except Exception as err:
            _LOGGER.warning("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
