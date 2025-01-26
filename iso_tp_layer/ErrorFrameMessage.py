import numpy as np
from dataclasses import dataclass
from FrameMessage import FrameMessage
from FrameType import FrameType


@dataclass
class ErrorFrameMessage(FrameMessage):
    serviceId: int
    errorCode: int

    def __init__(self, serviceId: int, errorCode: int):
        super().__init__(FrameType.ErrorFrame)
        self.serviceId = np.uint8(serviceId)
        self.errorCode = np.uint8(errorCode)
