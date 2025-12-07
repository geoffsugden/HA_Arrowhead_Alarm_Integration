"""Config flow for the Arrowhead Alarm Panel integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .arrowhead_alarm_api import ArrowheadAlarmAPI
from .const import (
    CONTROL_COUNT,
    CONTROL_NAME,
    CONTROL_NUMBER,
    CONTROLS,
    DOMAIN,
    ZONE_COUNT,
    ZONE_NAME,
    ZONE_NUMBER,
    ZONE_TYPE,
    ZONE_TYPES,
    ZONES,
)

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

    def __init__(self) -> None:
        """Initialize the Config Flow."""
        self.user_data: dict[str, Any] = {}
        self._zone_count: int = 0
        self._control_count: int = 0
        self._configured_zones: list[dict] = []
        self._configured_controls: list[dict] = []

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

                self.user_data = user_input
                return await self.async_step_setup_entity_counts()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_setup_entity_counts(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allows user to enter the number of zones."""
        schema = vol.Schema(
            {
                vol.Required(ZONE_COUNT, default=1): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=0, max=32),
                ),
                vol.Required(CONTROL_COUNT, default=0): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=0, max=4),
                ),
            }
        )

        if user_input is not None:
            self._zone_count = int(user_input[ZONE_COUNT])
            self._control_count = int(user_input[CONTROL_COUNT])

            if self._zone_count == 0 and self._control_count == 0:
                return self.async_create_entry(
                    title=f"Arrowhead Panel ({self.user_data[CONF_HOST]})",
                    data=self.user_data,
                )
            if self._zone_count > 0:
                return await self.async_step_setup_zones()

            return await self.async_step_setup_controls()

        return self.async_show_form(step_id="setup_entity_counts", data_schema=schema)

    async def async_step_setup_zones(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Sets up the zones for the Alarm Panel."""
        if user_input is not None:
            self._configured_zones.append(user_input)

        if len(self._configured_zones) >= self._zone_count:
            self.user_data[ZONES] = self._configured_zones
            if self._control_count > 0:
                return await self.async_step_setup_controls()

            return self.async_create_entry(
                title=f"Arrowhead Panel ({self.user_data[CONF_HOST]})",
                data=self.user_data,
            )

        current_index = len(self._configured_zones) + 1

        schema = vol.Schema(
            {
                vol.Required(ZONE_NUMBER, default=current_index): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                vol.Required(ZONE_NAME, default=f"Zone {current_index}"): str,
                vol.Required(ZONE_TYPE, default=ZONE_TYPES[0]): SelectSelector(
                    SelectSelectorConfig(
                        options=ZONE_TYPES, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="setup_zones",
            data_schema=schema,
            description_placeholders={
                "index": str(current_index),
                "count": str(self._zone_count),
            },
        )

    async def async_step_setup_controls(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Sets up the controls for the Alarm Panel."""
        if user_input is not None:
            self._configured_controls.append(user_input)

        if len(self._configured_controls) >= self._control_count:
            self.user_data[CONTROLS] = self._configured_controls

            if self._control_count > 0:
                return self.async_create_entry(
                    title=f"Arrowhead Panel ({self.user_data[CONF_HOST]})",
                    data=self.user_data,
                )

        current_index = len(self._configured_controls) + 1

        schema = vol.Schema(
            {
                vol.Required(CONTROL_NUMBER, default=current_index): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                vol.Required(CONTROL_NAME, default=f"Control {current_index}"): str,
            }
        )

        return self.async_show_form(
            step_id="setup_controls",
            data_schema=schema,
            description_placeholders={
                "index": str(current_index),
                "count": str(self._control_count),
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
