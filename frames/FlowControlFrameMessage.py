import numpy as np
from dataclasses import dataclass
from frames.FrameMessage import FrameMessage
from frames.FrameType import FrameType


@dataclass
class FlowControlFrameMessage(FrameMessage):
    flowStatus: int
    blockSize: int
    separationTime: int

    def __init__(self, flowStatus: int, blockSize: int, separationTime: int):
        super().__init__(FrameType.FlowControlFrame)
        self.flowStatus = np.uint8(flowStatus)
        self.blockSize = np.uint8(blockSize)
        self.separationTime = np.uint8(separationTime)

