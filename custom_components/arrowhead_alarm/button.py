"""Button platform for Arrowhead Alarm integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.exceptions import HomeAssistantError

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

    configured_controls = config_entry.data.get(CONTROLS, [])

    controls = [
        ArrowheadButton(
            coordinator=coordinator,
            control_id=control[CONTROL_NUMBER],
            name=control[CONTROL_NAME],
        )
        for control in configured_controls
    ]
    async_add_entities(controls)


class ArrowheadButton(CoordinatorEntity, ButtonEntity):
    """Representation of an Arrowhead Alarm button."""

    def __init__(self, coordinator, control_id: int, name: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._control_id = control_id
        self._attr_name = name
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_control_{control_id}"
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return information about the device."""
        # This links the button to the main alarm panel device
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "Arrowhead Alarm Panel",
            "manufacturer": "Arrowhead",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        api = self.coordinator.api

        try:
            await api.trigger_output(self._control_id)
        except ConnectionError as err:
            _LOGGER.error("Failed to trigger output %s: %s", self._control_id, err)
            raise HomeAssistantError(
                f"Failed to trigger output {self._control_id}"
            ) from err
