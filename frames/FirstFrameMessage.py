import numpy as np
from dataclasses import dataclass
from bitarray import bitarray
from frames.DataFrame import DataFrame
from frames.FrameType import FrameType


@dataclass
class FirstFrameMessage(DataFrame):
    dataLength: int

    def __init__(self, dataLength: int, data: bitarray):
        super().__init__(FrameType.FirstFrame, data)
        self.dataLength = np.uint16(dataLength)
