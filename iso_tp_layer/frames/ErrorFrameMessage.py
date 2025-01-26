import numpy as np
from dataclasses import dataclass
from iso_tp_layer.frames.FrameMessage import FrameMessage
from iso_tp_layer.frames.FrameType import FrameType


@dataclass
class ErrorFrameMessage(FrameMessage):
    serviceId: int
    errorCode: int

    def __init__(self, serviceId: int, errorCode: int):
        super().__init__(FrameType.ErrorFrame)
        self.serviceId = np.uint8(serviceId)
        self.errorCode = np.uint8(errorCode)
