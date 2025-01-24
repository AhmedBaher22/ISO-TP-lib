from dataclasses import dataclass
from frames.FrameType import FrameType


@dataclass
class FrameMessage:
    def __init__(self, frameType: FrameType):
        self.frameType = frameType
