"""Binary Sensors for Arrowhead Alarm Integration."""

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
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
    coordinator = config_entry.runtime_data.coordinator

    configured_zones = config_entry.data[ZONES]

    # Create a sensors list.
    async_add_entities(
        [ArrowheadBinarySensor(coordinator, zone) for zone in configured_zones]
    )


class ArrowheadBinarySensor(
    CoordinatorEntity[ArrowheadAlarmCoordinator], BinarySensorEntity
):
    """A binary sensor for an Arrowhead Alarm Zone."""

    def __init__(
        self, coordinator: ArrowheadAlarmCoordinator, zone_config: dict
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._zone_id: int = int(zone_config[ZONE_NUMBER])
        self._attr_name = zone_config[ZONE_NAME]
        self._attr_device_class = zone_config[ZONE_TYPE]
        self._attr_unique_id = f"{coordinator.entry_id}_zone_{self._zone_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry_id)},
            name="Arrowhead Alarm Panel",
            manufacturer="Arrowhead",
            model="ECi",
        )

    async def async_bypass_zone(self) -> None:
        """Service call to bypass this specific zone."""
        _LOGGER.info("Bypassing zone %s", self._zone_id)
        await self.coordinator.api.bypass_zone(self._zone_id)
        # Refresh to update the 'is_bypassed' attribute in the UI
        await self.coordinator.async_refresh()

    async def async_unbypass_zone(self) -> None:
        """Service call to unbypass this specific zone."""
        _LOGGER.info("Unbypassing zone %s", self._zone_id)
        await self.coordinator.api.unbypass_zone(self._zone_id)
        await self.coordinator.async_refresh()

    @property
    def is_on(self) -> bool:
        """Return True if the zone is Open/Active."""
        # This looks into the dictionary provided by the coordinator
        # Structure expected: {'zones': {1: True, 2: False}}
        return self.coordinator.data["zones"][self._zone_id]["open"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return attributes to display in the UI."""

        zone_data = self.coordinator.data["zones"][self._zone_id]

        return {
            "is_bypassed": zone_data["bypassed"],
            "in_alarm": zone_data["alarm"],
        }

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        # Check the state from the extra_state_attributes property's logic
        zone_data = self.coordinator.data["zones"][self._zone_id]

        if zone_data["alarm"]:
            # Use a distinctive icon for bypassed zones
            return "mdi:alarm-light"
        if zone_data["bypassed"]:
            return "mdi:shield-off-outline"

        # Fallback to the default icon for motion/open sensors
        return None
