"""The Arrowhead Alarm Panel integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .arrowhead_alarm_api import ArrowheadAlarmAPI
from .const import DOMAIN
from .coordinator import ArrowheadAlarmCoordinator
from .services import async_setup_services

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


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ArrowheadConfigEntry
) -> bool:
    """Set up Arrowhead Alarm Panel from a config entry."""

    host: str = config_entry.data[CONF_HOST]
    port: int = config_entry.data[CONF_PORT]
    api = ArrowheadAlarmAPI(host, port)

    coordinator = ArrowheadAlarmCoordinator(
        hass, api, config_entry.entry_id, config_entry.data
    )

    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = RuntimeData(coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(config_entry, _PLATFORMS)

    if not hass.services.has_service(DOMAIN, "disarm"):
        await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ArrowheadConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)

    if unload_ok:
        for service in ["bypass_zone", "unbypass_zone", "disarm"]:
            hass.services.async_remove(DOMAIN, service)

    return unload_ok
