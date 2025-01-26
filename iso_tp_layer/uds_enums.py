# uds_enums.py
from enum import Enum, auto

class SessionType(Enum):
    NONE = 0
    DEFAULT = 1
    EXTENDED = 2
    PROGRAMMING = 3

class OperationType(Enum):
    READ_DATA_BY_IDENTIFIER = auto()
    WRITE_DATA_BY_IDENTIFIER = auto()
    ECU_RESET = auto()
    TRANSFER_DATA = auto()
    REQUEST_DOWNLOAD = auto()
    REQUEST_TRANSFER_EXIT = auto()

class OperationStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    REJECTED = auto()