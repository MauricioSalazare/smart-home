from datetime import datetime, timezone
from dataclasses import dataclass, fields, asdict
import json
from dateutil import parser


@dataclass
class Message:
    """Dataclass to represent the relevant smart meter data from the MQTT broker"""

    timestamp_utc: datetime = None
    electricity_delivered_1: float = None
    electricity_delivered_2: float = None
    electricity_returned_1: float = None
    electricity_returned_2: float = None
    electricity_currently_delivered: float = None
    electricity_currently_returned: float = None
    phase_currently_delivered_l1: float = None
    phase_currently_delivered_l2: float = None
    phase_currently_delivered_l3: float = None
    phase_voltage_l1: float = None
    phase_voltage_l2: float = None
    phase_voltage_l3: float = None
    delivered: float = None  # Gas

    def is_complete(self) -> bool:
        """Check if all fields (except timestamp) are populated."""

        # noinspection PyUnresolvedReferences
        return all(
            getattr(self, field.name) is not None
            for field in self.__dataclass_fields__.values()
            if field.name != "timestamp_utc"
        )


@dataclass
class Reading:
    """Dataclass that represent the full data reading from the smart meter using REST-API interface"""

    mac_address: str
    gateway_model: str
    startup_time: datetime
    firmware_running: str
    firmware_available: str
    firmware_update_available: bool
    wifi_rssi: int
    mqtt_configured: bool
    mqtt_server: str  # This is new
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
    time_stamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0)
    )

    def __post_init__(self):
        # Type conversion map for easier management
        type_conversion = {
            float: float,
            int: int,
            bool: lambda x: x.lower() == "true",
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
                    raise ValueError(
                        f"Error converting field '{field.name}' with value '{value}' to {field_type}: {e}"
                    )

    def __repr__(self):
        return json.dumps(asdict(self), indent=4, default=str)
