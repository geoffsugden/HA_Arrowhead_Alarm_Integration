"""Binary Sensors for Arrowhead Alarm Integration."""

import logging

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ArrowheadConfigEntry
from .const import DOMAIN, ZONE_NAME, ZONE_NUMBER, ZONE_TYPE, ZONES
from .coordinator import ArrowheadAlarmCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ArrowheadConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensors."""
    # Get the coordinator from RuntimeData
    coordinator: ArrowheadAlarmCoordinator = config_entry.runtime_data.coordinator

    configured_zones = config_entry.data.get(ZONES, [])

    # Create a sensors list.
    sensors = [
        ArrowheadBinarySensor(
            coordinator=coordinator,
            zone_id=zone[ZONE_NUMBER],
            name=zone[ZONE_NAME],
            device_class=zone[ZONE_TYPE],
        )
        for zone in configured_zones
    ]

    async_add_entities(sensors)


class ArrowheadBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """A binary sensor for an Arrowhead Alarm Zone."""

    def __init__(self, coordinator, zone_id: int, name: str, device_class) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._attr_name = name
        self._attr_device_class = device_class
        self._zone_type = device_class
        # Unique ID allows UI editing
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_zone_{zone_id}"

    @property
    def is_on(self) -> bool:
        """Return True if the zone is Open/Active."""
        # This looks into the dictionary provided by the coordinator
        # Structure expected: {'zones': {1: True, 2: False}}
        zones = self.coordinator.data.get("zones", {})

        zone_state = zones.get(self._zone_id, {})

        return zone_state.get("open", False)

    @property
    def device_info(self) -> dict[str, Any]:
        """Return information about the device."""
        # This links the sensor back to the main device based on the config entry ID
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},  # type: ignore
            "name": "Arrowhead Alarm Panel",
            "manufacturer": "Arrowhead",
            # Add model, firmware, etc., if available from the API
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return attributes to display in the UI."""

        zone_data = self.coordinator.data["zones"].get(self._zone_id, {})

        is_bypassed = zone_data.get("bypassed", False)

        return {
            "is_bypassed": is_bypassed,
            "zone_type": self._zone_type,
        }

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        # Check the state from the extra_state_attributes property's logic
        zone_data = self.coordinator.data["zones"].get(self._zone_id, {})
        is_bypassed = zone_data.get("bypassed", False)

        if is_bypassed:
            # Use a distinctive icon for bypassed zones
            return "mdi:shield-off-outline"

        # Fallback to the default icon for motion/open sensors
        return None
