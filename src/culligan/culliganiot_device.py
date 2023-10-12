"""Class for devices handled by CulliganIoT domain"""

from .const import CULLIGAN_IOT_URL
from enum        import Enum, IntEnum, unique
from typing      import Any, Dict, Iterable, List, Optional, Set, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .uniapi_culliganiot import CulliganApi

#_LOGGER = getLogger(__name__)

PropertyName  = Union[str, Enum]
PropertyValue = Union[str, int, Enum]

class CulliganIoTDevice:
    """Generic device entity"""

    def __init__(self, culligan_api: "CulliganApi", device_dct: Dict):
        """
            Start object with serial = dsn. For some devices (such as SharkIQ vacuums) a device serial number is needed instead.
                call _update_metadata() to update these values.
                Other objects (such as Culligan water softeners), the DSN is used in place of serial numbers
        """
        self.culligan_api           = culligan_api

        self.properties             = {}

        # Properties
        self._name                  = device_dct['name']
        self._device_serial_number  = device_dct["serialNumber"]
        self._error                 = None

    @property
    def device_serial_number(self) -> Optional[str]:
        return self._device_serial_number

    @property
    def name(self):
        return self._name
    
    @property
    def all_properties_endpoint(self) -> str:
        """
            API endpoint to fetch updated device information
            This API retrieves all the properties for a specified device serial number (DSN).
        """
        return f'{CULLIGAN_IOT_URL}/device/data?serialNumber={self.device_serial_number}'
    
    def get_property_value(self, property_name: PropertyName) -> Any:
        """Get the value of a property from the properties dictionary"""
        if isinstance(property_name, Enum):
            property_name = property_name.value
        return self.properties[property_name]

    def update(self, property_list: Optional[Iterable[str]] = None):
        """Update the known device state from all properties and call _do_update to add the properties to the object property dictionary.
            Culligan returns all properties with each request."""
        full_update = True # property_list is None

        resp = self.culligan_api.self_request('get', self.all_properties_endpoint, params=None)
        properties = resp.json()
        
        return self._do_update(full_update, properties)

    async def async_update(self, property_list: Optional[Iterable[str]] = None):
        """Async update the known device state from all properties and call _do_update to add the properties to the object property dictionary
            Culligan returns all properties with each request."""
        full_update = True # property_list is None

        async with await self.culligan_api.async_request('get', self.all_properties_endpoint, params=None) as resp:
            properties = await resp.json()

        # _do_update should not be thread blocking
        return self._do_update(full_update, properties)

    def _do_update(self, full_update: bool, properties: Dict):
        """
            Update the internal state from fetched properties. This is called within update()/async_update()
            Categorize properties by Access (e.g. SET-able or Read-Only).
                Alternatively? This could use the read_only property bool instead of 'set_'.
        """

        # Update the property map so we can update by name instead of by fickle number
        if full_update:
            # Did a full update, so let's wipe everything
            self.properties = {}

        # Culligan properties are just a simple dict, no list of dicts
        datapoints = properties["data"]["datapoints"]

        for top_key in datapoints.keys():
            self.properties[top_key] = datapoints[top_key]

        # the nested datapoints don't seem interesting at the moment

        return True

    
class CulliganIoTSoftener(CulliganIoTDevice):
    """ Extend device into a water softener specific device """

    def __init__(self, culligan_api: "CulliganApi", device_dct: Dict):
        super().__init__(culligan_api, device_dct)

        self._model                     = device_dct["model"]
        self._generation                = device_dct["generation"]
        self._software_version          = device_dct["swVersion"]
        self._region                    = device_dct["region"]["code"]

        self.is_online                  = bool(device_dct["status"]["connection"]["online"])

    @property
    def device_model_number(self) -> Optional[str]:
        return self._model

    @property
    def generation(self):
        return self._generation
    
    @property
    def software_version(self):
        return self._software_version
    
    @property
    def region(self):
        return self._region