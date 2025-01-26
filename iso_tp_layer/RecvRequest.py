
from math import ceil
from typing import Callable
from bitarray import bitarray
from Exceptions import TimeoutException
import FrameMessage
from Address import Address
import time
from ErrorFrameMessage import ErrorFrameMessage
from FlowControlFrameMessage import FlowControlFrameMessage
from FlowStatus import FlowStatus
from InitialState import InitialState


class RecvRequest:
    """
    Represents a recv_request containing a bitarray message and a state.
    """
    def __init__(self, address: Address, block_size, timeout, stmin, on_success: Callable, on_error: Callable, send_frame: Callable):
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

    def set_flow_status(self, status: FlowStatus):
        self._flow_status = status

    def get_address(self):
        return self._address
    
    def get_message(self):
        return self._message

    def send_flow_control_frame(self):
        flow_control_frame = FlowControlFrameMessage(flowStatus=self._flow_status,
                                                     blockSize=self._max_block_size,
                                                     separationTime=self._stmin)
        self._send_frame(self._address, flow_control_frame)

    def send_error_frame(self):
        error_frame = ErrorFrameMessage(serviceId=0, errorCode=0)
        self._send_frame(self._address, error_frame)

    def set_max_block_size(self, max_block_size):
        self._max_block_size = max_block_size

    def set_current_block_size(self, current_block_size):
        self._current_block_size = current_block_size

    def get_data_length(self):
        return self._data_length

    def get_current_data_length(self):
        return ceil(len(self._message) / 8)  # Convert bits to bytes
    
    def set_data_length(self, data_length):
        self._data_length = data_length
    
    def get_current_block_size(self):
        return self._current_block_size

    def get_max_block_size(self):
        return self._max_block_size

    def set_expected_sequence_number(self, number):
        self._expected_sequence_number = number


    def get_expected_sequence_number(self):
        return self._expected_sequence_number

    def get_timeout(self):
        return self._timeout

    def get_stmin(self):
        return self._stmin

    def set_stmin(self, stmin):
        self._stmin = stmin

    def set_state(self, state):
        """
        Change the state of the recv_request.
        """
        self._state = state
        print(f"State has been changed to {state.__class__.__name__}")

    def get_state(self):
        return self._state.__class__.__name__

    def set_address(self, address: Address):
        self._address = address
        print(f"Address has been changed to {address}")


    def append_bits(self, bits: str):
        """
        Append bits to the message.
        """
        self._message.extend(bits)
        print(f"Bits appended: {bits}")
        print(f"Current message: {self._message.to01()}")


    def update_last_received_time(self):
        self._last_received_time = time.time()  # Update the last received time

    def get_last_received_time(self):
        return self._last_received_time


    def check_stmin(self):
        # True means you can proceed
        # False means you have to wait
        if self._stmin == 0:
            return True

        current_time = time.time()
        elapsed_time_ms = (current_time - self._last_received_time) * 1000  # Convert seconds to milliseconds

        return self._stmin <= elapsed_time_ms

    def process(self, frameMessage: FrameMessage):
        """
        Delegate processing to the current state.
        The state will modify the recv_request as needed.
        """
        current_time = time.time()
        elapsed_time_ms = (current_time - self._last_received_time) * 1000  # Convert seconds to milliseconds

        if 0 < self._timeout <= elapsed_time_ms:
            #
            # Some Logic !!
            #
            self.on_error(TimeoutException())

        self._state.handle(self, frameMessage)
