"""Binary Sensors for Arrowhead Alarm Integration."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ArrowheadConfigEntry
from .coordinator import ArrowheadAlarmCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ArrowheadConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the binary sensors."""
    # Get the coordinator from RuntimeData
    coordinator: ArrowheadAlarmCoordinator = config_entry.runtime_data.coordinator

    # --- BUILDING BLOCK STEP: Create ONE sensor manually ---
    sensors = [
        ArrowheadBinarySensor(
            coordinator=coordinator,
            zone_id=1,
            name="Garage Door",
            device_class=BinarySensorDeviceClass.GARAGE_DOOR,
        ),
        ArrowheadBinarySensor(
            coordinator=coordinator,
            zone_id=2,
            name="Garage PIR",
            device_class=BinarySensorDeviceClass.MOTION,
        ),
        ArrowheadBinarySensor(
            coordinator=coordinator,
            zone_id=3,
            name="Lounge PIR",
            device_class=BinarySensorDeviceClass.MOTION,
        ),
        ArrowheadBinarySensor(
            coordinator=coordinator,
            zone_id=4,
            name="Guest Room",
            device_class=BinarySensorDeviceClass.MOTION,
        ),
        ArrowheadBinarySensor(
            coordinator=coordinator,
            zone_id=5,
            name="Office",
            device_class=BinarySensorDeviceClass.MOTION,
        ),
        ArrowheadBinarySensor(
            coordinator=coordinator,
            zone_id=6,
            name="Master Bedroom PIR",
            device_class=BinarySensorDeviceClass.MOTION,
        ),
        ArrowheadBinarySensor(
            coordinator=coordinator,
            zone_id=7,
            name="Master Bedroom Door",
            device_class=BinarySensorDeviceClass.DOOR,
        ),
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
