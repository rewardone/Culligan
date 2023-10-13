"""
Simple implementation of the CulliganIoT API

This is used to provide an interface between Culligan and Ayla. 
Additional API endpoints are unknown and closed source.

Logging in directly to Ayla still works for some endpoints. 
Others such as /devices.json only seem to work when obtaining the token through Culligan.
"""

from aiohttp    import ClientSession             # async http
from ayla_iot_unofficial import AylaApi
from .culliganiot_device import CulliganIoTDevice, CulliganIoTSoftener
from datetime   import datetime, timedelta       # datetime operations
from requests   import post, put, request, Response   # http request library
from typing     import Dict, List, Optional      # object types

try:
    from ujson   import loads
except ImportError:
    from json    import loads

# Defined constants
from .const import (
    CULLIGAN_APP_ID,
    CULLIGAN_IOT_URL
)

# Custom error handling 
from .exc import (
    CulliganError,
    CulliganAuthExpiringError,
    CulliganNotAuthedError,
    CulliganAuthError,
    CulliganReadOnlyPropertyError,
)

_session = None

def new_culligan_api(username: str, password: str, app_id: str = CULLIGAN_APP_ID, websession: Optional[ClientSession] = None):
    """Get an CulliganApi object. Username is an email address."""
    return CulliganApi(username, password, app_id, websession=websession)


class CulliganApi:
    """Simple CulliganIoT Networks API wrapper"""

    def __init__(
            self,
            username: str,
            password: str,
            app_id: str,
            websession: Optional[ClientSession] = None):
        self._email                 = username      # username should always be an email address
        self._password              = password
        self._culligan_username     = None
        self._culligan_access_token = None
        self._culligan_refresh_token= None
        self._culligan_expiration   = None
        self._ayla_access_token     = None          # type: Optional[str]
        self._ayla_refresh_token    = None          # type: Optional[str]
        self._ayla_expiration       = None          # type: Optional[datetime]
        self._ayla_expiration_raw   = None          # type: Optional[int]
        self._is_authed             = False         # type: bool
        self._app_id                = app_id
        self.Ayla                   = None
        self.websession             = websession
        self.v1_url                 = CULLIGAN_IOT_URL

        # identify serials and dsns to track
        self.culligan_iot_serials   = []
        self.ayla_networks_dsns     = None

        # eventually combine them using Ayla 'softener' devices or other generic device class
        # ayla Softener(Device) class updates differently ... maybe extend Device here in Culligan

    async def ensure_session(self) -> ClientSession:
        """Ensure that we have an aiohttp ClientSession"""
        if self.websession is None:
            self.websession = ClientSession()
        return self.websession

    @property
    def _login_data(self) -> Dict[str, Dict]:
        """Prettily formatted data for the login flow"""
        return {
            "email": self._email,
            "password": self._password,
            "appId": self._app_id
        }

    @property
    def _sign_out_data(self) -> Dict:
        """Payload for the sign_out call"""
        return {"access_token": self._culligan_access_token}
    
    @property
    def _refresh_data(self) -> Dict:
        """Payload for refresh token call. Refresh tokens are currently long-lived and do not seem to change."""
        return {
            "refreshToken": self._culligan_refresh_token, 
            "appId": CULLIGAN_APP_ID
        }

    def _set_credentials(self, status_code: int, login_result: Dict):
        """Update the internal credentials store. This tracks current bearer token and data needed for token refresh."""
        if status_code   == 404:
            raise CulliganAuthError(login_result["error"]["message"] + " (Confirm login information is correct)")
        elif status_code == 401:
            raise CulliganAuthError(login_result["error"]["message"])
        elif status_code == 422:
            raise CulliganAuthError(login_result["error"]["message"] + " (Confirm login information is correct, username should be an email address.)")
        elif "data" not in login_result:
            raise CulliganAuthError(login_result + "Something unexpected happened and there was no 'data' in the response.")

        self._culligan_username     = login_result["data"]["userId"]
        self._culligan_access_token = login_result["data"]["accessToken"]
        self._culligan_refresh_token= login_result["data"]["refreshToken"]
        self._culligan_expiration   = datetime.now() + timedelta(seconds=login_result["data"]["expiresIn"])
        self._ayla_access_token     = login_result["data"]["linkedAccounts"]["ayla"]["access_token"]
        self._ayla_refresh_token    = login_result["data"]["linkedAccounts"]["ayla"]["refresh_token"]
        self._ayla_expiration       = datetime.now() + timedelta(seconds=login_result["data"]["linkedAccounts"]["ayla"]["expires_in"])
        self._ayla_expiration_raw   = login_result["data"]["linkedAccounts"]["ayla"]["expires_in"]

        if status_code != 200:
            self._is_authed   = False
        else:
            self._is_authed   = True

    def sign_in(self, returnResponse: bool = False):
        """ 
            Authenticate to Culligan API synchronously using a POST with credentials.
            Culligan may continue to hide/remove interactions with Ayla directly in the future.
                e.g. app_secret is no longer available and the previous app_secret no longer populates devices.json
            In the meantime, Culligan provides the ayla access_token directly to the user for direct use.
            To obtain an Ayla specific object (e.g. ayla_iot_unofficial AylaApi class object): 
            use returnResponse = True
            instantiate AylaApi
            then call AylaApi._set_credentials(200,resp["data"]["linkedAccounts"]["ayla"])
        """
        login_data = self._login_data   # get a map for JSON formatting
        resp = post(f"{self.v1_url:s}/auth/login", json=login_data)
        self._set_credentials(resp.status_code, resp.json())
        if returnResponse:
            return resp.json()

    def refresh_auth(self):
        """Refresh the authentication synchronously using object tracked refresh token."""
        refresh_data = self._refresh_data
        resp = put(f"{self.v1_url:s}/auth/login", json=refresh_data)
        self._set_credentials(resp.status_code, resp.json())

    async def async_sign_in(self):
        """Authenticate to Culligan API asynchronously using a POST with credentials.."""
        session = await self.ensure_session()
        login_data = self._login_data
        async with session.post(f"{self.v1_url:s}/auth/login", json=login_data) as resp:
            self._set_credentials(resp.status, await resp.json())

    async def async_refresh_auth(self):
        """Refresh the authentication asynchronously using object tracked refresh token.."""
        session = await self.ensure_session()
        refresh_data = self._refresh_data
        async with session.put(f"{self.v1_url:s}/auth/login", json=refresh_data) as resp:
            self._set_credentials(resp.status, await resp.json())

    def _clear_auth(self):
        """Clear authentication state"""
        self._is_authed             = False
        self._culligan_access_token = None
        self._culligan_refresh_token= None
        self._culligan_expiration   = None
        self._ayla_access_token     = None
        self._ayla_refresh_token    = None
        self._ayla_expiration       = None
        self.websession             = None

    def sign_out(self):
        """Sign out and invalidate the access token synchronously"""
        """Placeholder until logout is known"""
        #post(f"{self.v1_url:s}/auth/login", json=self._sign_out_data)
        self._clear_auth()

    async def async_sign_out(self):
        """Sign out and invalidate the access token asynchronously"""
        """Placeholder until logout is known"""
        session = await self.ensure_session()
        #async with session.post(f"{self.v1_url:s}/auth/login", json=self._sign_out_data) as _:
        #    pass
        #self._clear_auth()

    @property
    def auth_expiration(self) -> Optional[datetime]:
        """When does the auth expire"""
        if not self._is_authed:
            return None
        elif self._culligan_expiration is None:  # This should not happen, but let's be ready if it does...
            raise CulliganNotAuthedError("Invalid state.  Please reauthorize.")
        else:
            return self._culligan_expiration

    @property
    def token_expired(self) -> bool:
        """Return true if the token has already expired"""
        if self.auth_expiration is None:
            return True
        return datetime.now() > self.auth_expiration

    @property
    def token_expiring_soon(self) -> bool:
        """Return true if the token will expire soon"""
        if self.auth_expiration is None:
            return True
        return datetime.now() > self.auth_expiration - timedelta(seconds=600)  # Prevent timeout immediately following

    def check_auth(self, raise_expiring_soon=True):
        """Confirm authentication status"""
        if not self._culligan_access_token or not self._is_authed or self.token_expired:
            self._is_authed = False
            raise CulliganNotAuthedError()
        elif raise_expiring_soon and self.token_expiring_soon:
            raise CulliganAuthExpiringError()

    @property
    def auth_header(self) -> Dict[str, str]:
        self.check_auth()
        return {"Authorization": f"Bearer {self._culligan_access_token:s}"}
    
    @property
    def no_cache_header(self) -> Dict[str, str]:
        """If device/registry will be annoying later, can specify a force update using cache-control."""
        return {"Cache-Control": "no-cache"}

    def _get_headers(self, fn_kwargs) -> Dict[str, str]:
        """
        Extract the headers element from fn_kwargs, removing it if it exists
        and updating with self.auth_header.
        """
        try:
            headers = fn_kwargs['headers']
        except KeyError:
            headers = {}
        else:
            del fn_kwargs['headers']
        headers.update(self.auth_header)
        return headers

    def self_request(self, method: str, url: str, **kwargs) -> Response:
        """Perform an arbitrary request using the requests library synchronously"""
        headers = self._get_headers(kwargs)
        return request(method, url, headers=headers, **kwargs)

    async def async_request(self, http_method: str, url: str, **kwargs):
        """Perform an arbitrary request using the aiohttp library asynchronously"""
        session = await self.ensure_session()
        headers = self._get_headers(kwargs)
        return session.request(http_method, url, headers=headers, **kwargs)

    def get_ayla_api(self) -> AylaApi:
        """ Get an instace of the  AylaApi object and force instantiate it with auth provided by Culligan """
        AuthFromCulligan = {
            "access_token": self._ayla_access_token,
            "refresh_token": self._ayla_refresh_token,
            "expires_in": self._ayla_expiration_raw
        }
        Ayla = AylaApi(self._email, self._password, self._app_id, None, self.websession, False)
        Ayla._set_credentials(200, AuthFromCulligan)
        return Ayla

    def get_user_profile(self) -> Dict[str, str]:
        """Get user profile synchronously"""
        resp = self.self_request("get", f"{self.v1_url:s}/user/profile")
        response = resp.json()
        if resp.status_code == 401:
            raise CulliganAuthError(response)
        return response
    
    async def async_get_user_profile(self) -> Dict[str, str]:
        """Get user profile async"""
        async with await self.async_request("get", f"{self.v1_url:s}/user/profile") as resp:
            response = await resp.json()
            if resp.status == 401:
                raise CulliganAuthError(response)
        return response
    
    def get_metadata_user(self) -> Dict[str, str]:
        """Get user metadata synchronously. This is the CWS onboarding survey results (house side, what's new, interests, etc)"""
        resp = self.self_request("get", f"{self.v1_url:s}/metadata/user")
        response = resp.json()
        if resp.status_code == 401:
            raise CulliganAuthError(response)
        response["data"]["CWS-onboarding-survey"] = loads(response["data"]["CWS-onboarding-survey"])
        return response
    
    async def async_get_metadata_user(self) -> Dict[str, str]:
        """Get user metadata asynchronously. This is the CWS onboarding survey results (house side, what's new, interests, etc)"""
        async with await self.async_request("get", f"{self.v1_url:s}/metadata/user") as resp:
            response = await resp.json()
            if resp.status == 401:
                raise CulliganAuthError(response)
        response["data"]["CWS-onboarding-survey"] = loads(response["data"]["CWS-onboarding-survey"])
        return response
    
    def get_device_registry(self) -> Dict[str, str]:
        """Get device registry synchronously"""
        # returns data{devices[]}
        # devices has: serialNumber, name, model, generation, protocolVersion, lat, lon, swVersion, status{connection{online, lastUpdate}}, region{code}
        # metadata{}, registeredAt, createdAt, updatedAt, currentUserrole, dealerId, accountNumber, installationAddress{address, zip, city, state, country}
        resp = self.self_request("get", f"{self.v1_url:s}/device/registry")
        response = resp.json()
        if resp.status_code == 401:
            raise CulliganAuthError(response)
        
        # track serialNumbers for device/data endpoint
        for device in response["data"]["devices"]:
            if device["serialNumber"] not in self.culligan_iot_serials:
                self.culligan_iot_serials.append(device["serialNumber"])

        return response
    
    async def async_get_device_registry(self) -> Dict[str, str]:
        """Get device registry async"""
        async with await self.async_request("get", f"{self.v1_url:s}/device/registry") as resp:
            response = await resp.json()
            if resp.status == 401:
                raise CulliganAuthError(response)
            
        # track serialNumbers for device/data endpoint
        for device in response["data"]["devices"]:
            if device["serialNumber"] not in self.culligan_iot_serials:
                self.culligan_iot_serials.append(device["serialNumber"])

        return response
    
    def get_devices(self) -> List[CulliganIoTDevice]:
        """Retrieve a device object of devices. Ability to update with metadata. Synchronous."""
        devices = list()
        device_registry = self.get_device_registry()
        for d in device_registry["data"]["devices"]:
            # Have no idea what products will be enabled or how to identify them ... for now ... Smart HE is a softener
            if   d["name"] in ["Smart HE"]:
                devices.append(CulliganIoTSoftener(self, d))
            # Everything else is a device
            else:
                devices.append(CulliganIoTDevice  (self, d))
        return devices
    
    async def async_get_devices(self) -> List[CulliganIoTDevice]:
        """Retrieve a device object of devices. Ability to update with metadata. Asynchronous."""
        devices = list()
        device_registry = await self.async_get_device_registry()
        for d in device_registry["data"]["devices"]:
            # Have no idea what products will be enabled or how to identify them ... for now ... Smart HE is a softener
            if   d["name"] in ["Smart HE"]:
                devices.append(CulliganIoTSoftener(self, d))
            # Everything else is a device
            else:
                devices.append(CulliganIoTDevice  (self, d))
        return devices

    def get_device_data(self, serialNumber: str) -> Dict[str, str]:
        """Get device registry synchronously"""
        # most ayla properties in [data][datapoints]
        resp = self.self_request("get", f"{self.v1_url:s}/device/data?serialNumber={serialNumber:s}")
        response = resp.json()
        if resp.status_code == 401:
            raise CulliganAuthError(response)
        return response
    
    async def async_get_device_data(self, serialNumber: str) -> Dict[str, str]:
        """Get device registry async"""
        # most ayla properties in [data][datapoints]
        async with await self.async_request("get", f"{self.v1_url:s}/device/data?serialNumber={serialNumber:s}") as resp:
            response = await resp.json()
            if resp.status == 401:
                raise CulliganAuthError(response)
        return response