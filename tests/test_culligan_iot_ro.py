import asyncio

from culligan.culliganiot_device import CulliganIoTDevice, CulliganIoTRO, CulliganIoTSoftener
from culligan.uniapi_culliganiot import CulliganApi


def _smart_ro_registry_device(**overrides):
    device = {
        "serialNumber": "SRO1-0000AC000W024945974",
        "name": "Smart RO",
        "model": "SRO1",
        "generation": "1",
        "protocolVersion": 1,
        "swVersion": "1.2.3",
        "status": {"connection": {"online": True, "lastUpdate": "2026-05-12T00:00:00Z"}},
        "region": {"code": "US"},
    }
    device.update(overrides)
    return device


def _smart_he_registry_device():
    return {
        "serialNumber": "GBX2-HPRT979WPFARU4HZRMU",
        "name": "Smart HE",
        "model": "Smart HE gbx2",
        "generation": "2",
        "protocolVersion": 1,
        "swVersion": "2.3.4",
        "status": {"connection": {"online": True, "lastUpdate": "2026-05-12T00:00:00Z"}},
        "region": {"code": "US"},
    }


def _api_with_registry(devices):
    api = object.__new__(CulliganApi)
    api.get_device_registry = lambda: {"data": {"devices": devices}}

    async def async_get_device_registry():
        return {"data": {"devices": devices}}

    api.async_get_device_registry = async_get_device_registry
    return api


def test_culligan_iot_ro_is_read_only_device_type():
    api = object()
    device = CulliganIoTRO(api, _smart_ro_registry_device())

    assert isinstance(device, CulliganIoTDevice)
    assert device.name == "Smart RO"
    assert device.device_serial_number == "SRO1-0000AC000W024945974"
    assert device.device_model_number == "SRO1"
    assert device.software_version == "1.2.3"
    assert device.region == "US"
    assert device.is_online is True
    assert device.set_command_payload("bypass.permanent.on", True) is None


def test_get_devices_classifies_smart_ro_separately_from_softeners():
    api = _api_with_registry([_smart_ro_registry_device(), _smart_he_registry_device()])

    ro_device, softener_device = CulliganApi.get_devices(api)

    assert isinstance(ro_device, CulliganIoTRO)
    assert isinstance(softener_device, CulliganIoTSoftener)


def test_async_get_devices_classifies_smart_ro_separately_from_softeners():
    api = _api_with_registry([_smart_ro_registry_device(), _smart_he_registry_device()])

    ro_device, softener_device = asyncio.run(CulliganApi.async_get_devices(api))

    assert isinstance(ro_device, CulliganIoTRO)
    assert isinstance(softener_device, CulliganIoTSoftener)


def test_sro_serial_prefix_is_classified_as_ro_even_with_generic_name():
    api = _api_with_registry([_smart_ro_registry_device(name="Reverse Osmosis System")])

    [device] = CulliganApi.get_devices(api)

    assert isinstance(device, CulliganIoTRO)
