"""The component for the Arrowhead Alarm Panel (AAP) integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .coordinator import AAPCoordinator

PLATFORMS: list[Platform] = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


@dataclass
class RuntimeData:
    """Class to hold your data."""

    coordinator: DataUpdateCoordinator


AAPConfigEntry = ConfigEntry[RuntimeData]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up platform from a config entry."""

    # Initialise the coordinator that manages data updates from your api.
    # Defined in coordinator.py
    coordinator = AAPCoordinator(hass, config_entry)

    # Perform an initial data load from api.
    await coordinator.async_config_entry_first_refresh()

    # Initialise a listener for config flow options changes.
    # This will be removed automatically if the integraiton is unloaded.
    # See config_flow for defining an options setting that shows up as configure
    # on the integration.
    # If you do not want any config flow options, no need to have listener.
    config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )

    # Add the coordinator and update listener to config runtime data to make accessible throughout your integration
    config_entry.runtime_data = RuntimeData(coordinator)

    # Setup platforms (based on the list of entity types in PLATFORMS defined above)
    # This calls the async_setup method in each of your entity type files.
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, config_entry):
    """Handle config options update."""
    # Reload the integration when the options change.
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is where you would clean up when the user removes the integration.
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
