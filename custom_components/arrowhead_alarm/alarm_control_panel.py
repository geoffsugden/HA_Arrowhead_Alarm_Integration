"""Alarm control panel platform for Arrowhead Alarm."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
    CodeFormat,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ArrowheadAlarmCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
) -> None:
    """Set up alarm control panel from a config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([ArrowheadAlarmControlPanel(coordinator)])


class ArrowheadAlarmControlPanel(
    CoordinatorEntity[ArrowheadAlarmCoordinator], AlarmControlPanelEntity
):
    """Representation of an Arrowhead Alarm control panel."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
    )

    def __init__(self, coordinator: ArrowheadAlarmCoordinator) -> None:
        """Initialize the alarm control panel."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry_id}-alarm"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry_id)},
            "name": "Arrowhead Alarm",
        }

    @property
    def state(self) -> str | None:
        """Return the state of the alarm."""
        # status comes from your coordinator/API
        data = self.coordinator.data or {}
        status = str(data.get("partition_status", ""))

        # In alarm_control_panel.py -> alarm_state property
        mapping = {
            "partition_away_armed": AlarmControlPanelState.ARMED_AWAY,  # Matches 'A'
            "partition_stay_armed": AlarmControlPanelState.ARMED_HOME,  # Matches 'S'
            "partition_disarmed": AlarmControlPanelState.DISARMED,  # Matches 'D'
            "partition_in_alarm": AlarmControlPanelState.TRIGGERED,  # Matches 'AA'
            "partition_exit_away_timing": AlarmControlPanelState.ARMING,  # Matches 'EA'
            "partition_exit_stay_timing": AlarmControlPanelState.ARMING,  # Matches 'ES'
        }
        if status in mapping:
            return mapping.get(status)

        # If it's in the mapping, return that immediately
        if status in mapping:
            return mapping[status]

        # FALLBACK: If status is RO, NR, or AR, and it's not in the map above,
        # it means the panel is telling us it's idle/disarmed.
        if status in (
            "partition_ready",
            "partition_not_ready",
            "partition_alarm_restored",
        ):
            return AlarmControlPanelState.DISARMED

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self):
        """Add the 'Ready' status as an attribute."""
        status = self.coordinator.data.get("partition_status")
        return {
            "ready_to_arm": status == "RO",
            "raw_status": status,
        }

    @property
    def code_format(self) -> CodeFormat | None:
        """Return one of CodeFormat.NUMBER or CodeFormat.TEXT."""
        return CodeFormat.NUMBER

    @property
    def code_arm_required(self) -> bool:
        """Whether a code is required for arming."""
        return False

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        # Example: self.coordinator.api.send_disarm(code)
        await self.coordinator.api.disarm(pin=int(code) if code else 0, area=1)
        await self.coordinator.async_refresh()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.coordinator.api.arm_stay(area=1)
        await self.coordinator.async_refresh()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.coordinator.api.arm_away(area=1)
        await self.coordinator.async_refresh()

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        """Arm with custom bypass (Used here to bypass a specific zone)."""
        if code:
            # We treat the 'code' entered in the keypad as the Zone ID to bypass
            _LOGGER.info("Bypassing zone %s via alarm panel", code)
            await self.coordinator.api.bypass_zone(int(code))
            await self.coordinator.async_refresh()
        else:
            _LOGGER.warning("No zone ID (code) provided for bypass")
