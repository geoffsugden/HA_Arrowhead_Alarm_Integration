"""Services file for any calls to be exposed at top level."""

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import ArrowheadAlarmCoordinator

SERVICE_BYPASS_SCHEMA = vol.Schema(
    {
        vol.Required("zone_id"): cv.positive_int,
    }
)

SERVICE_DISARM_SCHEMA = vol.Schema(
    {
        vol.Required("pin"): cv.positive_int,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Setup the services for the Arrowhead Alarm Integration."""

    async def handle_alarm_action(call: ServiceCall):
        """Handle the service call."""
        config_entries = hass.config_entries.async_entries(DOMAIN)

        if not config_entries:
            return

        # For a single-panel setup, we grab the first loaded entry
        # and its typed coordinator from runtime_data
        config_entry = config_entries[0]
        coordinator: ArrowheadAlarmCoordinator = config_entry.runtime_data.coordinator

        zone_id: int | None = call.data.get("zone_id")
        pin: int | None = call.data.get("pin")

        if call.service == "bypass_zone" and zone_id:
            await coordinator.api.bypass_zone(zone_id)
        elif call.service == "unbypass_zone" and zone_id:
            await coordinator.api.unbypass_zone(zone_id)
        elif call.service == "disarm" and pin:
            await coordinator.api.disarm(pin)
        await coordinator.async_refresh()

    hass.services.async_register(
        DOMAIN,
        "bypass_zone",
        handle_alarm_action,
        schema=SERVICE_BYPASS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "unbypass_zone",
        handle_alarm_action,
        schema=SERVICE_BYPASS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "disarm",
        handle_alarm_action,
        schema=SERVICE_DISARM_SCHEMA,
    )
