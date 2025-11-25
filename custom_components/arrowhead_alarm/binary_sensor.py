"""Binary Sensors for Arrowhead Alarm Integration."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ArrowheadConfigEntry
from .const import DOMAIN
from .coordinator import ArrowheadAlarmCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ArrowheadConfigEntry,
):
    """Set up the binary sensors."""

    coordinator: ArrowheadAlarmCoordinator = config_entry.runtime_data.coordinator

    client = hass.data[DOMAIN]["client"]

    sensors = []


class ArrowheadBinarySensor(BinarySensorEntity):
    """A reed sensor for the AAP alarm system. Can be of type Door, Motion or Garage Door."""

    def __init__(self, client, zid, name, sensor_type) -> None:
        super().__init__()
