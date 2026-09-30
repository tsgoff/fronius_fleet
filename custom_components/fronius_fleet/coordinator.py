import datetime
import logging
from typing import Any

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

class FroniusFleetDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Fronius Fleet data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
        self.username = entry.data[CONF_USERNAME]
        self.password = entry.data[CONF_PASSWORD]
        # Create a dedicated session so cookies persist
        self.session: ClientSession = async_get_clientsession(hass)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=datetime.timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _login(self):
        """Login to Solar.web via Fronius Identity Provider to get session cookies."""
        import bs4
        
        login_start_url = "https://www.solarweb.com/Account/ExternalLogin"
        # 1. Start login flow, get redirect to OIDC
        resp1 = await self.session.get(login_start_url, allow_redirects=False)
        auth_url = resp1.headers.get("Location")
        if not auth_url:
            raise ValueError("OIDC Auth URL not found in Location header")

        # 2. Get the login page from login.fronius.com
        resp2 = await self.session.get(auth_url)
        text = await resp2.text()
        
        soup = bs4.BeautifulSoup(text, 'html.parser')
        form = soup.find('form', id='loginForm') or soup.find('form')
        if not form:
            raise ValueError("Login form not found on login.fronius.com")

        # 3. Extract hidden fields (sessionDataKey, authenticators, etc.)
        action = form.get('action')
        post_url = "https://login.fronius.com" + action.replace('../', '/')
        
        data = {}
        for input_tag in form.find_all('input'):
            name = input_tag.get('name')
            if name:
                data[name] = input_tag.get('value', '')
                
        # 4. Fill in credentials
        data['usernameUserInput'] = self.username
        data['username'] = self.username
        data['password'] = self.password
        data['chkRemember'] = 'on'
        
        # 5. Submit login form (allow_redirects=True will handle the callback automatically)
        await self.session.post(post_url, data=data, allow_redirects=True)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via Solar.web."""
        data_url = "https://www.solarweb.com/ActualData/GetActualValues?withOnlineState=True"
        list_url = "https://www.solarweb.com/PvSystems/GetPvSystemsForListView"
        
        try:
            response = await self.session.get(
                data_url, 
                headers={"X-Requested-With": "XMLHttpRequest"}
            )
            
            # If we are redirected to login, or unauthorized, try to login again
            if response.status != 200 or "Account/Login" in str(response.url):
                _LOGGER.debug("Session expired or missing, logging in again.")
                await self._login()
                response = await self.session.get(
                    data_url, 
                    headers={"X-Requested-With": "XMLHttpRequest"}
                )

            response.raise_for_status()
            items = await response.json()
            
            total_watts = 0.0
            total_energy_wh = 0.0
            online_count = 0
            total_count = len(items)
            
            for item in items:
                power = item.get("TotalPower")
                if power is not None:
                    total_watts += float(power)
                    online_count += 1
                
                # Check for total energy field. Usually it's TotalEnergy (Wh) or similar
                # HINT: If this field is incorrect, change it here based on network tab json response.
                energy = item.get("TotalEnergy") 
                if energy is not None:
                    total_energy_wh += float(energy)

            # Fetch list view for today's energy
            list_response = await self.session.get(
                list_url,
                headers={"X-Requested-With": "XMLHttpRequest"}
            )
            list_response.raise_for_status()
            list_data = await list_response.json()
            
            total_today_kwh = 0.0
            for pv in list_data.get("data", []):
                energy_today = pv.get("EnergyTodayInkWh")
                if energy_today is not None:
                    total_today_kwh += float(energy_today)

            # Calculate kW and GWh
            total_kw = round(total_watts / 1000.0, 1)
            total_gwh = round(total_energy_wh / 1_000_000_000.0, 2)
            
            return {
                "total_kw": total_kw,
                "total_gwh": total_gwh,
                "total_today_kwh": round(total_today_kwh, 2),
                "online_count": online_count,
                "total_count": total_count,
                "offline_count": total_count - online_count,
                "raw_data": items
            }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
