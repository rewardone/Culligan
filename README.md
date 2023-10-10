# Culligan
A discovery for Culligan smart water products

# Water Softener
The Excel sheet contains a listing of endpoints and what is needed for interaction with the Aylanetworks API. This data was gathered from proxy traffic. 

The powershell module is a way to interact with the endpoints via Powershell.

The python code is for packageability and publishing to PyPi as a module.

The softener does have an http webpage for wifi status and connect/disconnect. 
Local control of the device does not seem possible without understanding how Ayla sends commands to the device.

# Ayla References
This device is integrated by/with Ayla Networks and (generally) uses their documentation. 

See [Ayla-iot-unofficial](https://github.com/rewardone/ayla-iot-unofficial)

## Local Wifi Module Doc
Direct doc linked from the reference above: [salesforce doc](https://ayla.my.salesforce.com/sfc/p/#F00000005wvT/a/2A000000ZKSc/k2aXubMGof8Gooqm.nGLRqd.vyluxZLK9Qwe9xWUphQ)


## Installation
From PyPi
```bash
pip install culligan
```

Build from source
```bash
pip install build
pip build
pip install culligan
```

## Library Requirements
Requires typical http interaction and datatype packages like requests, aiohttp, ujson, and the ayla-iot-unofficial module to handle devices and communication.

## User Requirements
Reqiures a username and password (typically a smart device's app login credentials).
The Culligan specific app_id is included in the package (obtained from the Culligan app).

## Usage
### Class Object
Instantiate a new class object through new_culligan_api() or Culligan() directly.


### Access Tokens
The Culligan() object will call sign_in() automatically to obtain Culligan IoT and Ayla access_tokens. 
Then, it will instantiate an AylaApi() object with the Ayla access_token (no sign_in() required). 

Use Culligan for communication with the Culligan IoT domain.
Use the Ayla property of the Culligan object for direct communication with Ayla Networks.

### Devices
Gather devices by calling the Ayla.get_devices().

By default, calling get_devices() will return a list of class specific device objects with updated properties for use.

See ayla-iot-unofficial/device.py for implemented device classes.

## Typical Operation
```python
python3 -m pip install Culligan
```

```python
import Culligan

USERNAME = 'me@email.com'
PASSWORD = '$7r0nkP@s$w0rD'

CulliganApi = new_culligan_api(username, password)
CulliganApi.sign_in()
CulliganApi.Ayla = CulliganApi.get_ayla_api()

device_list = CulliganApi.Ayla.list_devices()
devices = CulliganApi.Ayla.get_devices()

# Example Water Softener Devices
softener = devices[0]

softener.capacity_remaining_gallons
softener.set_vacation_mode()
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
