"""
REST API for the smart-meter of my home
"""

import requests
from dataclasses import dataclass, field, fields, asdict
import json
from datetime import datetime, timezone
from dateutil import parser


#%%

@dataclass
class Reading:
    mac_address: str
    gateway_model: str
    startup_time: datetime
    firmware_running: str
    firmware_available: str
    firmware_update_available: bool
    wifi_rssi: int
    mqtt_configured: bool
    Equipment_Id: str
    GasEquipment_Id: str
    ElectricityTariff: float
    EnergyDeliveredTariff1: float
    EnergyDeliveredTariff2: float
    EnergyReturnedTariff1: float
    EnergyReturnedTariff2: float
    ReactiveEnergyDeliveredTariff1: float
    ReactiveEnergyDeliveredTariff2: float
    ReactiveEnergyReturnedTariff1: float
    ReactiveEnergyReturnedTariff2: float
    PowerDelivered_total: float
    PowerReturned_total: float
    PowerDelivered_l1: float
    PowerDelivered_l2: float
    PowerDelivered_l3: float
    PowerReturned_l1: float
    PowerReturned_l2: float
    PowerReturned_l3: float
    Voltage_l1: float
    Voltage_l2: float
    Voltage_l3: float
    Current_l1: float
    Current_l2: float
    Current_l3: float
    GasDelivered: float
    GasDeliveredHour: float
    PowerDeliveredHour: float
    PowerDeliveredNetto: float
    time_stamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0))
    def __post_init__(self):
        # Type conversion map for easier management
        type_conversion = {
            float: float,
            int: int,
            bool: lambda x: x.lower() == 'true',
            datetime: lambda x: parser.parse(x) if isinstance(x, str) else x,
        }

        for field in fields(self):
            value = getattr(self, field.name)
            field_type = field.type

            # Convert value only if it's not already of the correct type
            if not isinstance(value, field_type):
                try:
                    converter = type_conversion.get(field_type)
                    setattr(self, field.name, converter(value))
                except Exception as e:
                    raise ValueError(f"Error converting field '{field.name}' with value '{value}' to {field_type}: {e}")
    def __repr__(self):
        return json.dumps(asdict(self), indent=4, default=str)

#%%

# Define the URL of the REST-API server
url = "http://192.168.2.11:82/smartmeter/api/read"


#%%
response = requests.get(url)
if response.status_code == 200:
    # Parse the response as JSON
    json_data = response.json()
    # print("Successfully retrieved data:")
    # print(json_data)
    print(json.dumps(json_data, indent=4))
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")


#%%

#
#
# #%%
# while True:
#     try:
#         # Send a GET request to the server
#         response = requests.get(url)
#
#         # Check if the request was successful (status code 200)
#         if response.status_code == 200:
#             # Parse the response as JSON
#             json_data = response.json()
#             # print("Successfully retrieved data:")
#             # print(json_data)
#         else:
#             print(f"Failed to retrieve data. Status code: {response.status_code}")
#
#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred: {e}")
#
#
#     print(f"Power: {float(json_data['PowerDelivered_total']):.3f}")
#     time.sleep(3)