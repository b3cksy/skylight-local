from __future__ import annotations

import ipaddress

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_LAMP_IP, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LAMP_IP, default="0.0.0.0"): str,
        vol.Optional("name", default="Skylight Local"): str,
    }
)

async def _async_validate_input(hass: HomeAssistant, data: dict) -> dict:
    ipaddress.ip_address(data[CONF_LAMP_IP])

    return {"title": data.get("name") or "Skylight Local"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _async_validate_input(self.hass, user_input)
            except ValueError:
                errors[CONF_LAMP_IP] = "invalid_ip"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_LAMP_IP])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
