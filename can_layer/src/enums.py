from enum import Enum, auto

from enum import Enum, auto

class CANInterface(Enum):
    VECTOR = "vector"
    SOCKETCAN = "socketcan"
    KVASER = "kvaser"
    PCAN = "pcan"
    IXXAT = "ixxat"
    VIRTUAL = "virtual"

class CANBaudRate(Enum):
    RATE_125K = 125000
    RATE_250K = 250000
    RATE_500K = 500000
    RATE_1M = 1000000

class CANFrameFormat(Enum):
    STANDARD = auto()
    EXTENDED = auto()

class CANMode(Enum):
    NORMAL = auto()
    LISTEN_ONLY = auto()
    LOOPBACK = auto()

class LogLevel(Enum):
    INFO = "INFO"
    ERROR = "ERROR"
    WARNING = "WARNING"
    DEBUG = "DEBUG"