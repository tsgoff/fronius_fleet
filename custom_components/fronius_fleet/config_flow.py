import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_create_clientsession(hass)
    
    # We do a test login to verify credentials
    login_url = "https://www.solarweb.com/Account/Login"
    payload = {
        "Email": data[CONF_USERNAME],
        "Password": data[CONF_PASSWORD],
        "RememberMe": "true"
    }
    
    async with session.post(login_url, data=payload) as response:
        # Solar.web redirects on successful login or sets specific cookies.
        # Simple check: if login failed, they usually render the same page with errors.
        content = await response.text()
        if "Benutzername oder Passwort ist nicht korrekt" in content or "Incorrect email or password" in content:
            raise ValueError("invalid_auth")

    return {"title": "Fronius Solar.web Fleet"}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fronius Fleet."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
