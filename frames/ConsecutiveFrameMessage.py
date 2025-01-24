import numpy as np
from dataclasses import dataclass
from bitarray import bitarray
from frames.DataFrame import DataFrame
from frames.FrameType import FrameType


@dataclass
class ConsecutiveFrameMessage(DataFrame):
    sequenceNumber: int

    def __init__(self, sequenceNumber: int, data: bitarray):
        super().__init__(FrameType.ConsecutiveFrame, data)
        self.sequenceNumber = np.uint8(sequenceNumber)
