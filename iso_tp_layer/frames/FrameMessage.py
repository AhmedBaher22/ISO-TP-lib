from dataclasses import dataclass
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.frames.FrameType import FrameType


@dataclass
class FrameMessage:
    def __init__(self, frameType: FrameType):
        self.frameType = frameType
