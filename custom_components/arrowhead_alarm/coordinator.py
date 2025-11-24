"""Data Coordinator for AAP integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

__LOGGER = logging.getLogger(__name__)

class AAPCoordinator(DataUpdateCoordinator):
    """AAP coordinator."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        self.host = config_entry.data[CONF_HOST]
        self.port = config_entry.data[CONF_PORT]

        super().__init__(
            hass,
            __LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
        )





