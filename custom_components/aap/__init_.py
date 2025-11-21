"""The component for the Arrowhead Alarm Panel (AAP) integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import AAPCoordinator

# The domain of your component. Should match the name of your folder.
DOMAIN = "aap"


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up platform from a config entry."""

    # Initialise the coordinator that manages data updates from your api.
    # Defined in coordinator.py
    coordinator = AAPCoordinator(hass, config_entry)

    # This is where you would typically load your platforms (e.g., binary_sensor)
    # For now, we'll just store the entry data.
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = config_entry.data
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is where you would clean up when the user removes the integration.
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
