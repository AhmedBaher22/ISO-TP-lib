import numpy as np
from dataclasses import dataclass
from bitarray import bitarray
from DataFrame import DataFrame
from FrameType import FrameType


@dataclass
class SingleFrameMessage(DataFrame):
    dataLength: int

    def __init__(self, dataLength: int, data: bitarray):
        super().__init__(FrameType.SingleFrame, data)
        self.dataLength = np.uint8(dataLength)
