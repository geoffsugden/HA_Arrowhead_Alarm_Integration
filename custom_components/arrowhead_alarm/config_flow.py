"""Config flow for the Arrowhead Alarm Panel integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .arrowhead_alarm_api import ArrowheadAlarmAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input is correct.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Create a temporary API instance just to test connection
    api = ArrowheadAlarmAPI(data[CONF_HOST], data[CONF_PORT])

    try:
        # Attempt connection
        await api.connect()
        # If successful, close it immediately
        await api.close_connection()
    except Exception as err:
        _LOGGER.error("Failed to connect: %s", err)
        raise CannotConnect from err

    # Return the title required for the entry
    return {"title": f"Arrowhead Panel ({data[CONF_HOST]})"}


class ArrowHeadConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Arrowhead Alarm Panel."""

    VERSION = 1

    # TODO Setup Options Flow.

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info.get("title"))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
