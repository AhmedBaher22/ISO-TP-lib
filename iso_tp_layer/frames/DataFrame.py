from dataclasses import dataclass
from iso_tp_layer.frames.FrameMessage import FrameMessage
from bitarray import bitarray
from iso_tp_layer.frames.FrameType import FrameType


@dataclass
class DataFrame(FrameMessage):
    data: bitarray

    def __init__(self, frameType: FrameType, data: bitarray):
        super().__init__(frameType)
        self.data = data
