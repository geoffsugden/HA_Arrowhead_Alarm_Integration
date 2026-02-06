"""Binary Sensors for Arrowhead Alarm Integration."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ZONE_NAME, ZONE_NUMBER, ZONE_TYPE, ZONES
from .coordinator import ArrowheadAlarmCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
):
    """Set up the binary sensors."""
    # Get the coordinator from RuntimeData
    coordinator = entry.runtime_data.coordinator

    configured_zones = entry.data.get(ZONES, [])

    # Create a sensors list.
    async_add_entities(
        [ArrowheadBinarySensor(coordinator, zone) for zone in configured_zones]
    )


class ArrowheadBinarySensor(
    CoordinatorEntity[ArrowheadAlarmCoordinator], BinarySensorEntity
):
    """A binary sensor for an Arrowhead Alarm Zone."""

    def __init__(self, coordinator, zone_config) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._zone_id = zone_config[ZONE_NUMBER]
        self._attr_name = zone_config[ZONE_NAME]
        self._attr_device_class = zone_config[ZONE_TYPE]
        self._attr_unique_id = f"{coordinator.entry_id}_zone_{self._zone_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry_id)},
            "name": "Arrowhead Alarm Panel",
        }

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
        zones = self.coordinator.data.get("zones", {})

        return zones.get(self._zone_id, {}).get("open", False)

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return attributes to display in the UI."""

        zone_data = self.coordinator.data.get("zones", {}).get(self._zone_id, {})

        return {
            "is_bypassed": zone_data.get("bypassed", False),
            "in_alarm": zone_data.get("alarm", False),
        }

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        # Check the state from the extra_state_attributes property's logic
        zone_data = self.coordinator.data.get("zones", {}).get(self._zone_id, {})

        if zone_data.get("alarm"):
            # Use a distinctive icon for bypassed zones
            return "mdi:alarm-light"
        if zone_data.get("bypassed"):
            return "mdi:shield-off-outline"

        # Fallback to the default icon for motion/open sensors
        return None
