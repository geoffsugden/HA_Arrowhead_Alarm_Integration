"""Data Coordinator for AAP integration."""

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .arrowhead_alarm_api import ArrowheadAlarmAPI
from .const import DEFAULT_SCAN_INTERVAL, ZONES, CONTROLS, ZONE_NUMBER, CONTROL_NUMBER

_LOGGER = logging.getLogger(__name__)


class ArrowheadAlarmCoordinator(DataUpdateCoordinator):
    """Arrowhead_Alarm coordinator."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        self.host = config_entry.data[CONF_HOST]
        self.port = config_entry.data[CONF_PORT]
        self.api = ArrowheadAlarmAPI(self.host, self.port)
        self.listen_task: asyncio.Task | None = None
        self.poll_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        self.configured_zones = config_entry.data.get(ZONES, [])
        self.configured_controls = config_entry.data.get(CONTROLS, [])

        super().__init__(
            hass,
            _LOGGER,
            name=f"{HOMEASSISTANT_DOMAIN} ({config_entry.unique_id})",
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=self.poll_interval),
        )

        self.api.register_callback(self._async_handle_api_message)

    async def _async_handle_api_message(self, message: dict[str, Any]) -> None:
        """Callback: receive raw message, process it, update HA."""
        _LOGGER.debug("Coordinator received: %s", message)

        if "zone" in message and self.data and "zones" in self.data:
            zone_id = message["zone"]["zone_id"]
            status_type = message["zone"]["status_type"]
            action = message["zone"]["action"]

            # Create a copy of the current data for atomic update
            new_data = dict(self.data)
            new_zones = dict(new_data.get("zones", {}))

            current_zone = dict(new_zones.get(zone_id, {}))
            current_zone[status_type] = action

            new_zones[zone_id] = current_zone
            new_data["zones"] = new_zones

            self.async_set_updated_data(new_data)

    async def _async_update_data(self) -> dict[str, Any]:
        """Called periodically and during setup to connect and start listener."""

        try:
            if not self.api.is_connected:
                await self.api.connect()

            await self.api.set_mode(2)

            if self.data and "zones" in self.data:
                for z_id in self.data["zones"]:
                    self.data["zones"][z_id]["open"] = False
                    self.data["zones"][z_id]["open"] = False

            await self.api.request_status()

            if self.data is None:
                zones_data = {
                    z[ZONE_NUMBER]: {"open": False, "alarm": False, "bypassed": False}
                    for z in self.configured_zones
                }
                return {
                    "status": "online",
                    "area_1_state": "disarmed",
                    "zones": zones_data,
                }
            return self.data  # noqa: TRY300

        except Exception as err:
            _LOGGER.warning("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
