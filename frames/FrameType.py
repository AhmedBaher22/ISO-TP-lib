from enum import Enum


class FrameType(Enum):
    SingleFrame = 0,
    FirstFrame = 1,
    ConsecutiveFrame = 2,
    FlowControlFrame = 3,
    ErrorFrame = 4
