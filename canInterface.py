from enum import Enum, auto
import can
import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Callable, Tuple
from can.interfaces.vector.exceptions import VectorInitializationError

class LogLevel(Enum):
    INFO = "INFO"
    ERROR = "ERROR"
    WARNING = "WARNING"
    DEBUG = "DEBUG"
    
class CANLogger:
    def __init__(self, name: str, log_level: LogLevel, log_file: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.value))
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

class CANInterface(Enum):
    VECTOR = "vector"
    SOCKETCAN = "socketcan"
    KVASER = "kvaser"
    PCAN = "pcan"
    IXXAT = "ixxat"
    VIRTUAL = "virtual"

class CANBaudRate(Enum):
    RATE_125K = 125000
    RATE_250K = 250000
    RATE_500K = 500000
    RATE_1M = 1000000

class CANFrameFormat(Enum):
    STANDARD = auto()
    EXTENDED = auto()

class CANMode(Enum):
    NORMAL = auto()
    LISTEN_ONLY = auto()
    LOOPBACK = auto()

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
    data_bitrate: int = 2000000  # For CAN FD
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

class CANError(Exception):
    """Base class for CAN-related exceptions"""
    pass

class CANStatistics:
    def __init__(self):
        self.tx_count = 0
        self.rx_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.last_error_time = None
        self.bus_load = 0.0
        self.peak_bus_load = 0.0
        self.error_frames = 0

    def update_bus_load(self, load: float):
        self.bus_load = load
        self.peak_bus_load = max(self.peak_bus_load, load)

class CANCommunication:
    def __init__(self, config: CANConfig):
        self.config = config
        self.bus = None
        self.general_logger = CANLogger("GeneralLogger", LogLevel.INFO, "logs/can_general.log")
        self.error_logger = CANLogger("ErrorLogger", LogLevel.ERROR, "logs/can_error.log")
        
        # Message queues
        self.rx_queue = queue.Queue(maxsize=config.rx_queue_size)
        self.tx_queue = queue.Queue(maxsize=config.tx_queue_size)
        
        # Statistics
        self.statistics = CANStatistics()
        
        # Threading control
        self.running = False
        self.rx_thread = None
        self.tx_thread = None
        self._lock = threading.Lock()
        
        # Callback registry
        self.message_callbacks = {}
        self.error_callbacks = []
        
        # Bus state
        self.is_connected = False
        self.error_count = 0

    def start(self):
        """Start CAN communication and worker threads"""
        if not self.running:
            self.running = True
            self.connect()
            self.rx_thread = threading.Thread(target=self._rx_worker, daemon=True)
            self.tx_thread = threading.Thread(target=self._tx_worker, daemon=True)
            self.rx_thread.start()
            self.tx_thread.start()

    def stop(self):
        """Stop CAN communication and worker threads"""
        self.running = False
        if self.rx_thread:
            self.rx_thread.join()
        if self.tx_thread:
            self.tx_thread.join()
        self.disconnect()

    def _rx_worker(self):
        """Background thread for receiving messages"""
        while self.running:
            try:
                if not self.is_connected and self.config.auto_reconnect:
                    self._attempt_reconnect()
                    continue

                msg = self.bus.recv(timeout=0.1)
                if msg:
                    can_msg = self._convert_to_can_message(msg)
                    self.rx_queue.put(can_msg)
                    self.statistics.rx_count += 1
                    self._handle_callbacks(can_msg)

            except Exception as e:
                self._handle_error(e)

    def _tx_worker(self):
        """Background thread for sending messages"""
        while self.running:
            try:
                if not self.is_connected:
                    time.sleep(0.1)
                    continue

                msg = self.tx_queue.get(timeout=0.1)
                self._send_with_retry(msg)

            except queue.Empty:
                continue
            except Exception as e:
                self._handle_error(e)

    def register_callback(self, arbitration_id: int, callback: Callable[[CANMessage], None]):
        """Register a callback for specific message ID"""
        with self._lock:
            if arbitration_id not in self.message_callbacks:
                self.message_callbacks[arbitration_id] = []
            self.message_callbacks[arbitration_id].append(callback)

    def register_error_callback(self, callback: Callable[[Exception], None]):
        """Register a callback for error handling"""
        with self._lock:
            self.error_callbacks.append(callback)

    def send_message_async(self, msg: CANMessage) -> bool:
        """Asynchronously send a CAN message"""
        try:
            self.tx_queue.put(msg, timeout=0.1)
            return True
        except queue.Full:
            return False

    def receive_message(self, timeout: float = None) -> Optional[CANMessage]:
        """Receive a CAN message from the queue"""
        try:
            return self.rx_queue.get(timeout=timeout or self.config.timeout)
        except queue.Empty:
            return None

    def flush_queues(self):
        """Clear all message queues"""
        while not self.rx_queue.empty():
            self.rx_queue.get()
        while not self.tx_queue.empty():
            self.tx_queue.get()

    def get_bus_statistics(self) -> Dict:
        """Get current bus statistics"""
        stats = {
            'tx_count': self.statistics.tx_count,
            'rx_count': self.statistics.rx_count,
            'error_count': self.statistics.error_count,
            'bus_load': self.statistics.bus_load,
            'peak_bus_load': self.statistics.peak_bus_load,
            'uptime': time.time() - self.statistics.start_time,
            'error_frames': self.statistics.error_frames
        }
        return stats

    def set_bus_parameters(self, bitrate: int = None, data_bitrate: int = None):
        """Modify bus parameters on the fly"""
        if not self.is_connected:
            raise CANError("Cannot set parameters: Bus not connected")
        
        # Implementation depends on specific hardware support
        pass

    def _send_with_retry(self, msg: CANMessage) -> bool:
        """Internal method to send message with retry logic"""
        retries = self.config.retries
        while retries > 0:
            try:
                can_msg = self._convert_to_python_can_message(msg)
                self.bus.send(can_msg)
                self.statistics.tx_count += 1
                return True
            except Exception as e:
                retries -= 1
                if retries == 0:
                    self._handle_error(e)
                    return False
                time.sleep(0.1)

    def _handle_error(self, error: Exception):
        """Internal error handling method"""
        self.statistics.error_count += 1
        self.statistics.last_error_time = time.time()
        self.error_logger.logger.error(f"CAN Error: {str(error)}")
        
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception as e:
                self.error_logger.logger.error(f"Error in callback: {str(e)}")

        if self.statistics.error_count >= self.config.error_threshold:
            self.is_connected = False

    def _attempt_reconnect(self):
        """Attempt to reconnect to the CAN bus"""
        if not self.is_connected:
            try:
                self.connect()
                time.sleep(self.config.reconnect_delay)
            except Exception as e:
                self.error_logger.logger.error(f"Reconnection failed: {str(e)}")

    @staticmethod
    def _convert_to_can_message(msg: can.Message) -> CANMessage:
        """Convert python-can Message to internal CANMessage format"""
        return CANMessage(
            arbitration_id=msg.arbitration_id,
            data=msg.data,
            timestamp=msg.timestamp,
            is_extended_id=msg.is_extended_id,
            is_fd=msg.is_fd,
            is_remote_frame=msg.is_remote_frame,
            dlc=msg.dlc,
            channel=msg.channel
        )

    @staticmethod
    def _convert_to_python_can_message(msg: CANMessage) -> can.Message:
        """Convert internal CANMessage to python-can Message format"""
        return can.Message(
            arbitration_id=msg.arbitration_id,
            data=msg.data,
            is_extended_id=msg.is_extended_id,
            is_fd=msg.is_fd,
            is_remote_frame=msg.is_remote_frame,
            dlc=msg.dlc,
            channel=msg.channel
        )

    def _handle_callbacks(self, msg: CANMessage):
        """Handle registered callbacks for received messages"""
        callbacks = self.message_callbacks.get(msg.arbitration_id, [])
        for callback in callbacks:
            try:
                callback(msg)
            except Exception as e:
                self.error_logger.logger.error(f"Error in message callback: {str(e)}")
def message_callback(msg: CANMessage):
    print(f"Received message: {msg}")

def error_callback(error: Exception):
    print(f"Error occurred: {error}")

config = CANConfig(
    interface=CANInterface.VECTOR,
    channel=0,
    app_name="ISO-TP Layer",
    baud_rate=CANBaudRate.RATE_500K,
    frame_format=CANFrameFormat.STANDARD,
    mode=CANMode.NORMAL,
    auto_reconnect=True
)

can_comm = CANCommunication(config)
can_comm.register_callback(0x123, message_callback)
can_comm.register_error_callback(error_callback)

can_comm.start()

# Send message asynchronously
msg = CANMessage(arbitration_id=0x123, data=b'\x01\x02\x03\x04')
can_comm.send_message_async(msg)

# Get statistics
stats = can_comm.get_bus_statistics()
print(f"Bus statistics: {stats}")

# Clean shutdown
can_comm.stop()