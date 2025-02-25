import uuid
from math import ceil
from typing import Callable
from bitarray import bitarray
import time
import threading
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.frames.FlowControlFrameMessage import FlowControlFrameMessage
from iso_tp_layer.frames.FlowStatus import FlowStatus
from iso_tp_layer.Exceptions import TimeoutException
from iso_tp_layer.frames.FrameMessage import FrameMessage
from iso_tp_layer.Address import Address
from iso_tp_layer.recv_request.InitialState import InitialState
from iso_tp_layer.recv_request.ErrorState import ErrorState
from logger import Logger, LogType, ProtocolType


class RecvRequest:
    """
    Represents a recv_request containing a bitarray message and a state.
    """

    def __init__(self, address: Address, block_size, timeout, stmin, on_success: Callable, on_error: Callable,
                 send_frame: Callable):
        self._id = str(uuid.uuid4())[:8]   # Assign a unique ID
        self._address = address
        self._max_block_size = block_size
        self._timeout = timeout  # in milliseconds
        self._stmin = stmin  # in milliseconds
        self.on_success = on_success
        self.on_error = on_error
        self._send_frame = send_frame
        self._message = bitarray()  # Initialize with an empty bitarray
        self._state = InitialState()  # Start with the initial state
        self._expected_sequence_number = 1
        self._current_block_size = 0
        self._data_length = 0
        self._last_received_time = time.time()  # Store the time of last received message
        self._flow_status = FlowStatus.Continue
        self._timeout_thread = None
        self.logger = Logger(ProtocolType.ISO_TP)
        self.logger.log_message(
            log_type=LogType.RECEIVE,
            message=f"[RecvRequest-{self._id}] Initialized with address {self._address}, block_size={self._max_block_size}, timeout={self._timeout}ms"
        )

    def set_flow_status(self, status: FlowStatus):
        self._flow_status = status
        self.logger.log_message(
            log_type=LogType.RECEIVE,
            message=f"[RecvRequest-{self._id}] Flow status updated to {self._flow_status}"
        )

    def get_address(self):
        return self._address

    def get_message(self):
        return self._message

    def send_flow_control_frame(self):
        flow_control_frame = FlowControlFrameMessage(flowStatus=self._flow_status,
                                                     blockSize=self._max_block_size,
                                                     separationTime=self._stmin)
        self._send_frame(self._address, flow_control_frame)
        self.logger.log_message(
            log_type=LogType.RECEIVE,
            message=f"[RecvRequest-{self._id}] Sent Flow Control Frame: {flow_control_frame}"
        )

    def send_error_frame(self, e: Exception = Exception()):
        error_frame = FlowControlFrameMessage(flowStatus=FlowStatus.Abort, blockSize=0, separationTime=0)
        self._send_frame(self._address, error_frame)
        self.logger.log_message(
            log_type=LogType.WARNING,
            message=f"[RecvRequest-{self._id}] Sent Error Frame (Abort)"
        )
        self.logger.log_message(
            log_type=LogType.ERROR,
            message=f"[RecvRequest-{self._id}] {e}"
        )

    def set_max_block_size(self, max_block_size):
        self._max_block_size = max_block_size
        self.logger.log_message(
            log_type=LogType.RECEIVE,
            message=f"[RecvRequest-{self._id}] Max block size updated to {self._max_block_size}"
        )

    def set_current_block_size(self, current_block_size):
        self._current_block_size = current_block_size
        self.logger.log_message(
            log_type=LogType.RECEIVE,
            message=f"[RecvRequest-{self._id}] Current block size set to {self._current_block_size}"
        )

    def get_data_length(self):
        return self._data_length

    def get_current_data_length(self):
        return ceil(len(self._message) / 8)  # Convert bits to bytes

    def set_data_length(self, data_length):
        self._data_length = data_length
        self.logger.log_message(
            log_type=LogType.RECEIVE,
            message=f"[RecvRequest-{self._id}] Data length updated to {self._data_length} bytes"
        )

    def get_current_block_size(self):
        return self._current_block_size

    def get_max_block_size(self):
        return self._max_block_size

    def set_expected_sequence_number(self, number):
        self._expected_sequence_number = number
        self.logger.log_message(
            log_type=LogType.RECEIVE,
            message=f"[RecvRequest-{self._id}] Expected sequence number set to {self._expected_sequence_number}"
        )

    def get_expected_sequence_number(self):
        return self._expected_sequence_number

    def get_timeout(self):
        return self._timeout

    def get_stmin(self):
        return self._stmin

    def set_stmin(self, stmin):
        self._stmin = stmin
        self.logger.log_message(
            log_type=LogType.RECEIVE,
            message=f"[RecvRequest-{self._id}] STmin updated to {self._stmin}ms"
        )

    def set_state(self, state):
        """
        Change the state of the recv_request.
        """
        self._state = state
        if self._state.__class__.__name__ in {"ErrorState", "FinalState"}:
            self.logger.log_message(
                log_type=LogType.RECEIVE,
                message=f"[RecvRequest-{self._id}] State changed to {self._state.__class__.__name__}"
            )

    def get_state(self):
        return self._state.__class__.__name__

    def set_address(self, address: Address):
        self._address = address
        self.logger.log_message(
            log_type=LogType.RECEIVE,
            message=f"[RecvRequest-{self._id}] Address updated to {self._address}"
        )

    def append_bits(self, bits: str):
        """
        Append bits to the message.
        """
        self._message.extend(bits)
        self.logger.log_message(
            log_type=LogType.RECEIVE,
            message=f"[RecvRequest-{self._id}] Appended bits: {bitarray(bits).tobytes().hex().upper()} | "
                    f"Current message (HEX): {self._message.tobytes().hex().upper()} | Length: {len(self._message)//8} bytes"
        )



    def get_last_received_time(self):
        return self._last_received_time

    def start_timeout_timer(self):
        """
        Starts a timer that monitors for timeouts.
        If no message is received within `self._timeout` milliseconds, an exception is raised.
        """

        def monitor_timeout():
            if self._timeout == 0:
                return

            while True:
                if self._state.__class__.__name__ in {"ErrorState", "FinalState"}:
                    break

                time.sleep(self._timeout/1000)
                elapsed_time_ms = (time.time() - self._last_received_time) * 1000

                if self._state.__class__.__name__ in {"ErrorState", "FinalState"}:
                    break

                if elapsed_time_ms >= self._timeout:
                    self.logger.log_message(
                        log_type=LogType.ERROR,
                        message=f"[RecvRequest-{self._id}] Timeout occurred after {elapsed_time_ms:.2f} ms"
                    )
                    self.set_state(ErrorState())  # Transition to ErrorState
                    self.on_error(TimeoutException())
                    break  # Exit thread when timeout occurs

        self._timeout_thread = threading.Thread(target=monitor_timeout, daemon=True)
        self._timeout_thread.start()

    def reset_timeout_timer(self):
        """
        Resets the timeout timer whenever a new message is received.
        """
        self._last_received_time = time.time()
        self.logger.log_message(
            log_type=LogType.RECEIVE,
            message=f"[RecvRequest-{self._id}] Timeout timer reset"
        )


    def process(self, frameMessage: FrameMessage):
        """
        Delegate processing to the current state.
        The state will modify the recv_request as needed.
        """
        try:
            self._state.handle(self, frameMessage)
        except Exception as e:
            self.logger.log_message(
                log_type=LogType.ERROR,
                message=f"{e}"
            )
