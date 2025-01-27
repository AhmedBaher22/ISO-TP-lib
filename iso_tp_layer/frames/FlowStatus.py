from enum import Enum


class FlowStatus(Enum):
    Continue = 0
    Wait = 1
    Abort = 2
    Unknown = 3  # Added Unknown state

    @classmethod
    def _missing_(cls, value):
        # Handle invalid values by returning the Unknown state
        return cls.Unknown
