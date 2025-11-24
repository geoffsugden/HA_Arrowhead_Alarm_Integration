"""Binary Sensors for AAP Integration."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AAPConfigEntry  # type: ignore
from .const import DOMAIN
from .coordinator import AAPCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AAPConfigEntry,
):
    """Set up the binary sensors."""

    coordinator: AAPCoordinator = config_entry.runtime_data.coordinator

    client = hass.data[DOMAIN]["client"]

    sensors = []

    for zid, name in client.zones.items():
        sensors.append(AAPBinary_Sensor(client, zid, name, sensor_type))


class AAPBinary_Sensor(BinarySensorEntity):
    """A sensor for the AAP alarm system. Can be of type Door, Motion or Garage Door."""

    def __init__(self, client, zid, name, sensor_type) -> None:
        super().__init__()
