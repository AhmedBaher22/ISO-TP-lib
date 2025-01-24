from enum import Enum


class FlowStatus(Enum):
    Continue = 0,
    Wait = 1,
    Abort = 2
