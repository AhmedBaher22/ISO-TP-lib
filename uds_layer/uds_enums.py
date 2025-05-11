from enum import Enum, auto


class SessionType(Enum):
    NONE = 0
    DEFAULT = 1
    PROGRAMMING = 2
    EXTENDED = 3
    


class OperationType(Enum):
    READ_DATA_BY_IDENTIFIER = auto()
    WRITE_DATA_BY_IDENTIFIER = auto()
    ECU_RESET = auto()
    TRANSFER_DATA = auto()
    REQUEST_DOWNLOAD = auto()
    REQUEST_TRANSFER_EXIT = auto()
    COMMUNICATION_CONTROL =auto()
    ERASE_MEMORY=auto()

class OperationStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    REJECTED = auto()

class CommunicationControlSubFunction(Enum):
    ENABLE_RX_AND_TX = 0x00
    ENABLE_RX_DISABLE_TX = 0x01
    DISABLE_RX_ENABLE_TX = 0x02
    DISABLE_RX_AND_TX = 0x03

class CommunicationControlType(Enum):
    NORMAL_COMMUNICATION = 0x00
    NETWORK_MANAGEMENT = 0x01
    BOTH_COMMUNICATION_TYPES = 0x02