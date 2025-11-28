"""The Arrowhead Alarm Panel integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .coordinator import ArrowheadAlarmCoordinator

_PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]

type ArrowheadConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Class to hold your data."""

    coordinator: ArrowheadAlarmCoordinator


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ArrowheadConfigEntry
) -> bool:
    """Set up Arrowhead Alarm Panel from a config entry."""

    coordinator = ArrowheadAlarmCoordinator(hass, config_entry)

    await coordinator.async_config_entry_first_refresh()

    # Test to see if api initialised correctly, else raise ConfigNotReady to make HA retry setup
    # TODO if not coordinator.api.connected:
    #     raise ConfigEntryNotReady

    # TODO Initialise a listener for config flow options changes.

    config_entry.runtime_data = RuntimeData(coordinator)

    await hass.config_entries.async_forward_entry_setups(config_entry, _PLATFORMS)

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Delete device if selected from UI."""
    # Adding this function shows the delete device option in the UI.
    # Remove this function if you do not want that option.
    # You may need to do some checks here before allowing devices to be removed.
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ArrowheadConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
