from dataclasses import dataclass
from bitarray import bitarray
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.frames.FrameType import FrameType
from iso_tp_layer.frames.FrameMessage import FrameMessage

@dataclass
class DataFrame(FrameMessage):
    data: bitarray

    def __init__(self, frameType: FrameType, data: bitarray):
        super().__init__(frameType)
        self.data = data
