from dataclasses import dataclass
from FrameMessage import FrameMessage
from bitarray import bitarray
from FrameType import FrameType


@dataclass
class DataFrame(FrameMessage):
    data: bitarray

    def __init__(self, frameType: FrameType, data: bitarray):
        super().__init__(frameType)
        self.data = data
