"""Data Coordinator for AAP integration."""

from collections.abc import Mapping
import copy
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .arrowhead_alarm_api import ArrowheadAlarmAPI
from .const import ZONE_NUMBER, ZONES

_LOGGER = logging.getLogger(__name__)


class ArrowheadAlarmCoordinator(DataUpdateCoordinator):
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

    def _get_initial_data(self) -> dict[str, Any]:
        """Return the default data structure."""
        zones_init = {
            z[ZONE_NUMBER]: {"open": False, "alarm": False, "bypassed": False}
            for z in self.configured_zones
        }
        return {
            "partition_status": "D",
            "zones": zones_init,
        }

    async def _async_handle_api_message(self, message: dict[str, Any]) -> None:
        """Process push messages from the API."""

        msg_type = message.get("type")
        msg_data = message.get("data")

        # Handle Command Responses (Success/Error)
        if msg_type == "command_response" and msg_data:
            if msg_data["status"] == "error":
                _LOGGER.error("Alarm Panel returned Error Code: %s", msg_data["code"])
                # Optional: Fire a Home Assistant event so you can trigger a notification
                self.hass.bus.fire("arrowhead_alarm_error", {"code": msg_data["code"]})
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
        new_data = copy.deepcopy(self.data)

        # --- 1. HANDLE SYNC START ---
        if msg_type == "sync_start":
            self._sync_in_progress = True
            self._received_zones.clear()
            return  # No need to update state yet

        if not msg_data:
            return

        # --- 3. HANDLE ZONE UPDATES ---
        if msg_type == "zone":
            zone_id = int(msg_data["zone_id"])
            # status_type = msg_data["status_type"]
            # action = msg_data["action"]

            # If we are in the middle of a status dump, track this zone ID
            if self._sync_in_progress:
                self._received_zones.add(zone_id)

            # Update the zone in our data structure
            if zone_id in new_data["zones"]:
                # new_data["zones"][zone_id][status_type] = action
                new_zones = dict(new_data["zones"])
                new_zones[zone_id] = dict(new_zones[zone_id])
                new_zones[zone_id][msg_data["status_type"]] = msg_data["action"]
                new_data["zones"] = new_zones
        # --- 2. HANDLE PARTITION UPDATES & SYNC CLEANUP ---
        elif msg_type == "partition":
            new_status = msg_data["status"]
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
            if msg_data["raw_code"] == "RO" and self._sync_in_progress:
                for zid in new_data["zones"]:
                    if zid not in self._received_zones:
                        new_data["zones"][zid]["bypassed"] = False
                        new_data["zones"][zid]["open"] = False
                        new_data["zones"][zid]["alarm"] = False

                self._sync_in_progress = False

        # --- 4. FINALIZE ---
        # This pushes the update to all entities (binary sensors, switches, alarm panel)
        self.async_set_updated_data(new_data)

    async def _async_update_data(self) -> dict[str, Any]:
        """Called periodically and during setup to connect and start listener."""

        try:
            if not self.api.is_connected:
                await self.api.connect()

            await self.api.set_mode(2)
            await self.api.request_status()

            if self.data is None:
                zones_init = {
                    z[ZONE_NUMBER]: {"open": False, "alarm": False, "bypassed": False}
                    for z in self.configured_zones
                }
                return {
                    "partition_status": "D",
                    "zones": zones_init,
                }
            return self.data  # noqa: TRY300

        except Exception as err:
            _LOGGER.warning("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
