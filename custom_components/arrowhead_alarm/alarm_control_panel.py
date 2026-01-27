"""Alarm control panel platform for Arrowhead Alarm."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_ARM_NIGHT,
    SERVICE_ALARM_ARM_VACATION,
    SERVICE_ALARM_DISARM,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up alarm control panel from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        ArrowheadAlarmControlPanel(coordinator, entry),
    ]

    async_add_entities(entities)


class ArrowheadAlarmControlPanel(AlarmControlPanelEntity):
    """Representation of an Arrowhead Alarm control panel."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_VACATION
    )

    def __init__(self, coordinator: Any, entry: ConfigEntry) -> None:
        """Initialize the alarm control panel."""
        self.coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}-alarm"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Arrowhead Alarm",
        }

    @property
    def state(self) -> str | None:
        """Return the state of the alarm."""
        if not self.coordinator.data:
            return None

        # Map coordinator data to alarm state
        # TODO: Implement state mapping based on coordinator data
        return STATE_ALARM_DISARMED

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        # TODO: Implement disarm logic
        pass

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        # TODO: Implement arm home logic
        pass

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        # TODO: Implement arm away logic
        pass

    async def async_added_to_hass(self) -> None:
        """Subscribe to coordinator updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator update."""
        self.async_write_ha_state()
