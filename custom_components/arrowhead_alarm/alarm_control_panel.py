"""Alarm control panel platform for Arrowhead Alarm."""

from __future__ import annotations

from typing import Any
import asyncio
import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
    CodeFormat,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from . import ArrowheadConfigEntry
from .const import DOMAIN
from .coordinator import ArrowheadAlarmCoordinator, ArrowheadData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ArrowheadConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up alarm control panel from a config entry."""
    coordinator = config_entry.runtime_data.coordinator
    async_add_entities([ArrowheadAlarmControlPanel(coordinator)])


class ArrowheadAlarmControlPanel(
    CoordinatorEntity[ArrowheadAlarmCoordinator], AlarmControlPanelEntity
):
    """Representation of an Arrowhead Alarm control panel."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_NIGHT
    )

    def __init__(self, coordinator: ArrowheadAlarmCoordinator) -> None:
        """Initialize the alarm control panel."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry_id}-alarm"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry_id)},
            name="Arrowhead Alarm Panel",
            manufacturer="Arrowhead",
            model="ECi",
        )

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state of the alarm."""
        # status comes from your coordinator/API
        status = self.coordinator.data["partition_status"]

        if not status:
            return None

        # In alarm_control_panel.py -> alarm_state property
        mapping: dict[str, AlarmControlPanelState] = {
            "partition_away_armed": AlarmControlPanelState.ARMED_AWAY,  # Matches 'A'
            "partition_stay_armed": AlarmControlPanelState.ARMED_HOME,  # Matches 'S'
            "partition_disarmed": AlarmControlPanelState.DISARMED,  # Matches 'D'
            "partition_in_alarm": AlarmControlPanelState.TRIGGERED,  # Matches 'AA'
            "partition_exit_away_timing": AlarmControlPanelState.ARMING,  # Matches 'EA'
            "partition_exit_stay_timing": AlarmControlPanelState.ARMING,  # Matches 'ES'
        }

        if state := mapping.get(status):
            return state
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
    def extra_state_attributes(self) -> dict[str, Any]:
        """Add the 'Ready' status as an attribute."""
        status = self.coordinator.data["partition_status"]
        return {
            "ready_to_arm": status == "partition_ready",
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
        if not code or not code.isdigit():
            _LOGGER.warning("Disarm attempted without a valid numeric PIN")
        else:
            await self.coordinator.api.disarm(pin=code, area=1)
            await self.coordinator.async_refresh()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.coordinator.api.arm_stay(area=1)
        await self.coordinator.async_refresh()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.coordinator.api.arm_away(area=1)
        await self.coordinator.async_refresh()

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Arm with custom bypass of zone 3. Customised specifcally for this site."""
        bypass_zone = 3
        if code and code.isdigit():
            bypass_zone = int(code)

        _LOGGER.info("Bypassing zone %s via alarm panel", bypass_zone)
        await self.coordinator.api.bypass_zone(bypass_zone)
        # sleep for 1 second to make sure bypass makes it to alarm
        await asyncio.sleep(1)
        await self.coordinator.api.arm_stay(area=1)
        await self.coordinator.async_refresh()
