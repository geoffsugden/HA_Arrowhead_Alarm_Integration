"""Data Coordinator for AAP integration."""

import logging
import asyncio
from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .arrowhead_alarm_api import ArrowheadAlarmAPI

_LOGGER = logging.getLogger(__name__)


class ArrowheadAlarmCoordinator(DataUpdateCoordinator):
    """Arrowhead_Alarm coordinator."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        self.host = config_entry.data[CONF_HOST]
        self.port = config_entry.data[CONF_PORT]
        self.api = ArrowheadAlarmAPI(self.host, self.port)
        self.listen_task: asyncio.Task | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{HOMEASSISTANT_DOMAIN} ({config_entry.unique_id})",
        )

        self.api.register_callback(self._async_handle_api_message)

    async def _async_handle_api_message(self, message: dict[str, Any]) -> None:
        """Callback: receive raw message, process it, update HA."""
        _LOGGER.debug("Coordinator received: %s", message)

        if "zone" in message and self.data and "zones" in self.data:
            zone_id = message["zone"]["zone_id"]
            status_type = message["zone"]["status_type"]
            action = message["zone"]["action"]

            # 1. Create a copy of the current data for atomic update
            new_data = dict(self.data)

            if "zones" not in new_data:
                new_data["zones"] = {}

            # 2. Get the current zone states, or initizalise if needed
            current_zone_state = new_data["zones"].get(zone_id, {})

            # 3. Update the specific status_type (e.g. 'open') for the zone
            current_zone_state[status_type] = action

            # 4. Update the main dictionary and notify HA
            new_data["zones"][zone_id] = current_zone_state
            self.async_set_updated_data(new_data)

    async def _async_update_data(self) -> dict[str, Any]:
        """Called once during setup to connect and start listener"""

        try:
            if not self.api.is_connected:
                await self.api.connect()

            if not self.listen_task or self.listen_task.done():
                self.listen_task = self.hass.async_create_task(self.api.listen())

            await self.api.set_mode(2)

            return {  # noqa: TRY300
                "status": "online",
                "area_1_state": "disarmed",
                "zones": {
                    1: {
                        "open": False,
                        "alarm": False,
                        "bypassed": False,
                    },
                },
            }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
