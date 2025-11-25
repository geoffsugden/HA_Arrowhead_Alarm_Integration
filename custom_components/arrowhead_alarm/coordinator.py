"""Data Coordinator for AAP integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from arrowhead_alarm_api import ArrowheadAlarmAPI

__LOGGER = logging.getLogger(__name__)


class ArrowheadAlarmCoordinator(DataUpdateCoordinator):
    """Arrowhead_Alarm coordinator."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        self.host = config_entry.data[CONF_HOST]
        self.port = config_entry.data[CONF_PORT]

        super().__init__(
            hass,
            __LOGGER,
            name=f"{HOMEASSISTANT_DOMAIN} ({config_entry.unique_id})",
        )

        self.api = ArrowheadAlarmAPI(self.host, self.port)
