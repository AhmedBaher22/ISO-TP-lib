from dataclasses import dataclass
from typing import Optional
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from can_layer.enums import CANInterface, CANBaudRate, CANFrameFormat, CANMode


@dataclass
class CANConfig:
    interface: CANInterface
    channel: int
    app_name: str
    baud_rate: CANBaudRate = CANBaudRate.RATE_500K
    frame_format: CANFrameFormat = CANFrameFormat.STANDARD
    mode: CANMode = CANMode.NORMAL
    fd_flag: bool = False
    bitrate_switch: bool = False
    data_bitrate: int = 2000000
    timeout: float = 5.0
    retries: int = 3
    rx_queue_size: int = 1000
    tx_queue_size: int = 1000
    auto_reconnect: bool = True
    reconnect_delay: float = 1.0
    error_threshold: int = 10


@dataclass
class CANMessage:
    arbitration_id: int
    data: bytes
    timestamp: float
    is_extended_id: bool = False
    is_fd: bool = False
    is_remote_frame: bool = False
    dlc: Optional[int] = None
    channel: Optional[int] = None


@dataclass
class CANFilter:
    can_id: int
    can_mask: int
    extended: bool = False
