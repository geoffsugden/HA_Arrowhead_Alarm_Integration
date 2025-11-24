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
from .credentials import host, port, user

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, description={"suggested_value": host}): str,
        vol.Required(CONF_PORT, description={"suggested_value": port}): str,
        vol.Required("user", description={"suggest_value": user}): int,
        vol.Required("zones", description={"suggested_value": 7}): int,
        vol.Required("outputs", description={"suggest_value", 1}): int,
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry[Any]) -> OptionsFlow:
        """Get the options flow for this handler."""
        return AAPOptionsFlowHandler(config_entry)


class AAPOptionsFlowHandler(OptionsFlow):
    """Handle options for the AAP integration.

    1. Binary Sensors, each will have a Name, Zone and Device_Type
    2. Outputs, each will have a Name and Zone. Type will be button
    3. Alarm Panel, User will enter a pin, this will be saved unique for this integration.
    """

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry
        self.zones = dict(config_entry.options.get("zones", {}))
        self.outputs = dict(config_entry.options.get("outputs", {}))

    async def async_step_init(self, user_input=None):
        """User to edit as required."""

        if user_input is not None:
            if user_input["choice"] == "zones":
                return await self.async_step_zones()
            elif user_input["choice"] == "outputs":
                return await self.async_step_outputs()

        choices = {"zones": "Edit Zones", "outputs": "Edit Outputs"}
        schema = vol.Schema({vol.Required("choice"): vol.In(choices)})
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_zones(self, user_input=None):
        """Allow zone configuration with freindly names."""

        schema_dict = {}

        if not self.zones:
            # Up to 32 Zones available as standard. Pre fill up to this number
            for i in range(1, 32):
                self.zones[str(i)] = f"Zone {i}"
        for zid, name in self.zones.items():
            schema_dict[vol.Optional(zid, default=name)] = str

        if user_input is not None:
            new_zones = {zid: user_input[zid] for zid in user_input}
            self.zones = new_zones
            return await self._save_options()

        return self.async_show_form(
            step_id="zones", data_schema=vol.Schema(schema_dict)
        )

    async def async_step_outputs(self, user_input=None):
        """Allow output configuration with freindly names."""

        schema_dict = {}

        if not self.outputs:
            # Up to outputs available as standard. Pre fill up to this number
            for i in range(1, 4):
                self.outputs[str(i)] = f"Zone {i}"
        for oid, name in self.outputs.items():
            schema_dict[vol.Optional(oid, default=name)] = str

        if user_input is not None:
            new_outputs = {oid: user_input[oid] for oid in user_input}
            self.outputs = new_outputs
            return await self._save_options()

        return self.async_show_form(
            step_id="outputs", data_schema=vol.Schema(schema_dict)
        )

    async def _save_options(self):
        """Persist updated options to entry."""

        new_options = {**self.config_entry.options}
        new_options["zones"] = self.zones
        new_options["outputs"] = self.outputs

        self.hass.config_entries.async_update_entry(
            self.config_entry, options=new_options
        )

        return self.async_create_entry(title="", data={})
