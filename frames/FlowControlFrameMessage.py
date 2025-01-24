import numpy as np
from dataclasses import dataclass
from frames.FlowStatus import FlowStatus
from frames.FrameMessage import FrameMessage
from frames.FrameType import FrameType


@dataclass
class FlowControlFrameMessage(FrameMessage):
    flowStatus: FlowStatus
    blockSize: int
    separationTime: int

    def __init__(self, flowStatus: FlowStatus, blockSize: int, separationTime: int):
        super().__init__(FrameType.FlowControlFrame)
        self.blockSize = np.uint8(blockSize)
        self.separationTime = np.uint8(separationTime)

