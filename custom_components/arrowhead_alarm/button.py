"""Button platform for Arrowhead Alarm integration. This allows use to configure controls e.g. Open/Close a Garage Door."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ArrowheadConfigEntry
from .const import CONTROL_NAME, CONTROL_NUMBER, CONTROLS, DOMAIN
from .coordinator import ArrowheadAlarmCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ArrowheadConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities for Arrowhead Alarm."""
    coordinator: ArrowheadAlarmCoordinator = config_entry.runtime_data.coordinator

    configured_controls = config_entry.data[CONTROLS]

    controls = [
        ArrowheadButton(
            coordinator=coordinator,
            control_id=control[CONTROL_NUMBER],
            name=control[CONTROL_NAME],
        )
        for control in configured_controls
    ]
    async_add_entities(controls)


class ArrowheadButton(CoordinatorEntity[ArrowheadAlarmCoordinator], ButtonEntity):
    """Representation of an Arrowhead Alarm button."""

    def __init__(
        self, coordinator: ArrowheadAlarmCoordinator, control_id: int, name: str
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._control_id = control_id
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.entry_id}_control_{control_id}"
        self._attr_has_entity_name = True

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry_id)},
            name="Arrowhead Alarm Panel",
            manufacturer="Arrowhead",
            model="ECi",
        )

    async def async_press(self) -> None:
        """Handle the button press."""

        try:
            await self.coordinator.api.trigger_output(self._control_id)
        except ConnectionError as err:
            _LOGGER.error("Failed to trigger output %s: %s", self._control_id, err)
            raise HomeAssistantError(
                f"Failed to trigger output {self._control_id}"
            ) from err
