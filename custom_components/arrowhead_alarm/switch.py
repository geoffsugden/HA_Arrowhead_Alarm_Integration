"""Switch platform for Arrowhead Alarm zone bypassing."""

from __future__ import annotations
import asyncio
from typing import Any
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ZONE_NAME, ZONE_NUMBER, ZONES
from .coordinator import ArrowheadAlarmCoordinator

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up bypass switches from a config entry."""
    coordinator = entry.runtime_data.coordinator
    configured_zones = entry.data.get(ZONES, [])

    async_add_entities(
        [ArrowheadBypassSwitch(coordinator, zone) for zone in configured_zones]
    )


class ArrowheadBypassSwitch(CoordinatorEntity[ArrowheadAlarmCoordinator], SwitchEntity):
    """A switch to bypass/unbypass a zone."""

    def __init__(
        self, coordinator: ArrowheadAlarmCoordinator, zone_config: dict
    ) -> None:
        """Initialize the bypass switch."""
        super().__init__(coordinator)
        self._zone_id = zone_config[ZONE_NUMBER]
        self._attr_name = f"Bypass {zone_config[ZONE_NAME]}"
        self._attr_unique_id = f"{coordinator.entry_id}_bypass_{self._zone_id}"
        self._attr_icon = "mdi:shield-off"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry_id)},
            "name": "Arrowhead Alarm Panel",
        }

    @property
    def is_on(self) -> bool:
        """Return True if the zone is currently bypassed."""
        zones = self.coordinator.data.get("zones", {})
        return zones.get(self._zone_id, {}).get("bypassed", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Bypass the zone."""
        await self.coordinator.api.bypass_zone(self._zone_id)
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unbypass the zone."""
        z_id = self._zone_id
        await self.coordinator.api.unbypass_zone(self._zone_id)
        await asyncio.sleep(2.0)
        await self.coordinator.async_refresh()
