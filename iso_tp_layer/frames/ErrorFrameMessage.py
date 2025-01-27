import numpy as np
from dataclasses import dataclass
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.frames.FrameType import FrameType
from iso_tp_layer.frames.FrameMessage import FrameMessage


@dataclass
class ErrorFrameMessage(FrameMessage):
    serviceId: int
    errorCode: int

    def __init__(self, serviceId: int, errorCode: int):
        super().__init__(FrameType.ErrorFrame)
        self.serviceId = np.uint8(serviceId)
        self.errorCode = np.uint8(errorCode)
