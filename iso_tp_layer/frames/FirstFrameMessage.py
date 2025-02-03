import numpy as np
from dataclasses import dataclass
from bitarray import bitarray
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.frames.DataFrame import DataFrame
from iso_tp_layer.frames.FrameType import FrameType

@dataclass
class FirstFrameMessage(DataFrame):
    dataLength: int

    def __init__(self, dataLength: int, data: bitarray):
        super().__init__(FrameType.FirstFrame, data)
        self.dataLength = np.uint16(dataLength)

    def __str__(self):
        """Return a human-readable string representation of the object."""
        return f"FirstFrameMessage(dataLength={self.dataLength}, data={self.data.tobytes().hex().upper()})"
