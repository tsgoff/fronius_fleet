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
    
    import bs4
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }

    # We do a test login to verify credentials using the new OIDC flow
    login_start_url = "https://www.solarweb.com/Account/ExternalLogin"
    resp1 = await session.get(login_start_url, headers=headers, allow_redirects=False)
    auth_url = resp1.headers.get("Location")
    if not auth_url:
        raise ValueError("unknown")

    resp2 = await session.get(auth_url, headers=headers)
    text = await resp2.text()
    
    soup = bs4.BeautifulSoup(text, 'html.parser')
    form = soup.find('form', id='loginForm') or soup.find('form')
    if not form:
        raise ValueError("unknown")

    action = form.get('action')
    post_url = "https://login.fronius.com" + action.replace('../', '/')
    
    post_data = {}
    for input_tag in form.find_all('input'):
        name = input_tag.get('name')
        if name:
            post_data[name] = input_tag.get('value', '')
            
    post_data['usernameUserInput'] = data[CONF_USERNAME]
    post_data['username'] = data[CONF_USERNAME]
    post_data['password'] = data[CONF_PASSWORD]
    post_data['chkRemember'] = 'on'
    
    resp3 = await session.post(post_url, data=post_data, headers=headers, allow_redirects=True)
    if "login.fronius.com" in str(resp3.url) and "retry" in str(resp3.url):
        raise ValueError("invalid_auth")
        
    text3 = await resp3.text()
    soup3 = bs4.BeautifulSoup(text3, 'html.parser')
    form3 = soup3.find('form')
    if form3:
        post_url3 = form3.get('action')
        if not post_url3.startswith("http"):
            post_url3 = "https://login.fronius.com" + post_url3
        post_data3 = {}
        for input_tag in form3.find_all('input'):
            name = input_tag.get('name')
            if name:
                post_data3[name] = input_tag.get('value', '')
        
        await session.post(post_url3, data=post_data3, headers=headers, allow_redirects=True)

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
