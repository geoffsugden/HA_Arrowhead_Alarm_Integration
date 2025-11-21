"""Config Flow for AAP Integration."""

from __future__ import annotations

import logging
from typing import Any

# from .arrowheadapi import ArrowheadAPI
import credentials
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

__LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, description={"suggested_value": credentials.host}): str,
        vol.Required(CONF_PORT, description={"suggested_value": credentials.port}): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate that the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # ArrowheadAPI.validate_set_mode(CONF_HOST, CONF_PORT)

    return {"title": f"AAP Integration - {data[CONF_HOST]}"}
