import numpy as np
from dataclasses import dataclass
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.frames.FlowStatus import FlowStatus
from iso_tp_layer.frames.FrameMessage import FrameMessage
from iso_tp_layer.frames.FrameType import FrameType


@dataclass
class FlowControlFrameMessage(FrameMessage):
    flowStatus: FlowStatus
    blockSize: int
    separationTime: int

    def __init__(self, flowStatus: FlowStatus, blockSize: int, separationTime: int):
        super().__init__(FrameType.FlowControlFrame)
        self.flowStatus = flowStatus
        self.blockSize = np.uint8(blockSize)
        self.separationTime = np.uint8(separationTime)

