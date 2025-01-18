from datetime import datetime
from dataclasses import dataclass

@dataclass
class Message:
    """Dataclass to represent the specific subtopics to record."""
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
