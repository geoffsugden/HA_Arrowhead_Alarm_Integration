"""Config Flow for AAP Integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .arrowheadapi import ArrowheadAPI
from .const import DOMAIN
from .credentials import host, port

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, description={"suggested_value": host}): str,
        vol.Required(CONF_PORT, description={"suggested_value": port}): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate that the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    instance = ArrowheadAPI(host, port)

    success, message = await instance.validate_set_mode(CONF_HOST, CONF_PORT)

    return {"title": "AAP Integration", "success": success, "message": message}


class AAPConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for the AAP Integration."""

    VERSION = 1
    _input_data: dict[str, Any]

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry: ConfigEntry[Any]) -> OptionsFlow:
    #     """Get the options flow for this handler."""
    #     return AAPOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            # Form has been filled in and submitted.
            try:
                info = await validate_input(self.hass, user_input)
            # TODO Implement some exception handling that isn't shit. But for now we're just protoyping.
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if "base" not in errors:
                # Validation was succesful. Create a unique id and continue.
                await self.async_set_unique_id(info.get("title"))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)  # type: ignore  # noqa: PGH003

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )  # type: ignore  # noqa: PGH003
