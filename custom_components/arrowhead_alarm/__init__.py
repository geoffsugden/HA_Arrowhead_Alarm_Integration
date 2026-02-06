"""The Arrowhead Alarm Panel integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .arrowhead_alarm_api import ArrowheadAlarmAPI
from .const import DOMAIN
from .coordinator import ArrowheadAlarmCoordinator

_PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.ALARM_CONTROL_PANEL,
]

type ArrowheadConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Class to hold your data."""

    coordinator: ArrowheadAlarmCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ArrowheadConfigEntry) -> bool:
    """Set up Arrowhead Alarm Panel from a config entry."""

    api = ArrowheadAlarmAPI(entry.data[CONF_HOST], entry.data[CONF_PORT])

    coordinator = ArrowheadAlarmCoordinator(hass, api, entry.entry_id, entry.data)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = RuntimeData(coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    async def handle_alarm_action(call):
        """Handle the service call."""
        zone_id = call.data.get("zone_id")
        pin = call.data.get("pin")
        if call.service == "bypass_zone":
            await coordinator.api.bypass_zone(zone_id)
        elif call.service == "unbypass_zone":
            await coordinator.api.unbypass_zone(zone_id)
        else:
            await coordinator.api.disarm(pin)
        await coordinator.async_refresh()

    hass.services.async_register(DOMAIN, "bypass_zone", handle_alarm_action)
    hass.services.async_register(DOMAIN, "unbypass_zone", handle_alarm_action)
    hass.services.async_register(DOMAIN, "disarm", handle_alarm_action)

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
