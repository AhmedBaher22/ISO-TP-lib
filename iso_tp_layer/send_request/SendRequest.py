from typing import Callable
import threading
import time
from bitarray import bitarray
import sys
import os
# Add the package root directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.Address import Address
from iso_tp_layer.Exceptions import MessageLengthExceededException, FlowStatusAbortException, \
    InvalidFlowStatusException, TimeoutException
from iso_tp_layer.frames.FlowStatus import FlowStatus


class SendRequest:
    def __init__(self, txfn: Callable, rxfn: Callable, on_success: Callable,
                 on_error: Callable, address: Address, timeout=0,
                 stmin=0, block_size=0, tx_padding=0xFF):
        self._tx_padding = tx_padding  # Default padding value
        self._txfn = txfn
        self._rxfn = rxfn
        self._on_success = on_success
        self._on_error = on_error
        self._stmin = stmin
        self._timeout = timeout
        self._block_size = block_size
        self._address = address
        self._data = b""  # Initialize the data attribute
        self._remaining_data = b""
        self._index = 0
        self._sequence_num = 0
        self._block_counter = 0
        self._isFinished = False
        self._received_error_frame = False  # New attribute for error frame tracking

    def set_received_error_frame(self, value: bool):
        self._received_error_frame = value

    def get_received_error_frame(self) -> bool:
        return self._received_error_frame

    def is_finished(self):
        return self._isFinished

    def has_received_error_frame(self):
        return self._received_error_frame

    def send(self, data: bitarray):
        """Entry point to send data."""
        try:
            self._data = data.tobytes()  # Set the class attribute
            byte_length = len(self._data)

            if byte_length <= 7:
                self._send_single()
            else:
                self._send_first()
        except Exception as e:
            print(f"Error during send: {e}")
            self._on_error(e)

    def _send_single(self):
        """Send a single frame message."""
        try:
            first_byte = (0x0 << 4) | (len(self._data) & 0x0F)
            frame = bytes([first_byte]) + self._data.ljust(7, self._tx_padding.to_bytes(1, 'little'))
            hex_frame = frame.hex()
            print(f"Single frame (hex): {hex_frame}")
            self._txfn(self._address, hex_frame)
            self._end_request()  # Successful completion
        except Exception as e:
            print(f"Error in _send_single: {e}")
            self._on_error(e)

    def _send_first(self):
        """Send the first frame of a multi-frame message."""
        try:
            message_length = len(self._data)
            if message_length > 4095:
                # "Message length exceeds the maximum limit of 4095 bytes for ISO-TP."
                raise MessageLengthExceededException()

            first_byte = (0x1 << 4) | ((message_length >> 8) & 0x0F)
            second_byte = message_length & 0xFF
            first_frame_data = self._data[:6]
            frame = bytes([first_byte, second_byte]) + first_frame_data
            hex_frame = frame.hex()
            print(f"First frame (hex): {hex_frame}")
            self._txfn(self._address, hex_frame)

            # Start listening for control frames in a separate thread
            listener_thread = threading.Thread(
                target=self.listen_for_control_frame,
                args=(self._send_consecutive,),
                daemon=True
            )
            listener_thread.start()

        except Exception as e:
            print(f"Error in _send_first: {e}")
            self._on_error(e)

    def _send_consecutive(self):
        """Send consecutive frames of a multi-frame message."""
        try:
            if not self._remaining_data:
                self._remaining_data = self._data[6:]  # Initialize with the remaining data after the first frame

            while self._index < len(self._remaining_data):
                if self._received_error_frame:
                    return

                if 0 < self._block_size <= self._block_counter:
                    print(f"block_counter: {self._block_counter}\nblock_size: {self._block_size}")
                    print("Block size limit reached. Waiting for next control frame...")
                    listener_thread = threading.Thread(
                        target=self.listen_for_control_frame,
                        args=(self._reset_block_counter,),
                        daemon=True
                    )
                    listener_thread.start()
                    return

                if self._stmin > 0:
                    print(f"Sleeping for {self._stmin / 100.0}")
                    time.sleep(self._stmin / 100.0)

                first_byte = (0x2 << 4) | (self._sequence_num & 0x0F)
                frame = bytes([first_byte]) + self._remaining_data[self._index:self._index + 7].ljust(7,
                                                                                                      self._tx_padding.to_bytes(
                                                                                                          1, 'little'))
                hex_frame = frame.hex()
                print(f"Consecutive frame (hex): {hex_frame}")
                self._txfn(self._address, hex_frame)

                self._index += 7
                self._sequence_num = (self._sequence_num + 1) % 16
                self._block_counter += 1

            self._end_request()
        except Exception as e:
            print(f"Error in _send_consecutive: {e}")
            self._on_error(e)

    def listen_for_control_frame(self, callBackFn: Callable):
        """Thread function to listen for control frames."""
        try:
            if self._received_error_frame:
                return
            is_control_frame_received = False
            start_time = time.time()  # Record the start time
            while not is_control_frame_received:
                elapsed_time_ms = (time.time() - start_time) * 1000
                if elapsed_time_ms > self._timeout:
                    # "Timeout Elapsed!"
                    raise TimeoutException()

                control_frame = self._rxfn(self._address)
                if not control_frame:
                    print("Still waiting for a valid control frame...")
                    time.sleep(0.1)
                    continue

                flow_status_value = control_frame[0] & 0x0F
                flow_status = FlowStatus(flow_status_value)

                block_size = control_frame[1]
                stmin = control_frame[2]
                self._stmin = stmin
                self._block_size = block_size

                if flow_status == FlowStatus.Continue:
                    print("Flow status: Continue to send.")
                    is_control_frame_received = True
                elif flow_status == FlowStatus.Wait:
                    print("Flow status: Wait.")
                    while not is_control_frame_received:
                        time.sleep(stmin / 100.0)
                        is_control_frame_received = True
                elif flow_status == FlowStatus.Abort:
                    # "Flow status: Abort received. Transmission terminated."
                    raise FlowStatusAbortException()
                else:
                    # f"Invalid flow status received: {flow_status_value}"
                    raise InvalidFlowStatusException(flow_status_value)

            if is_control_frame_received:
                callBackFn()
        except Exception as e:
            print(f"Error in listen_for_control_frame: {e}")
            self._on_error(e)

    def _reset_block_counter(self):
        """Callback function to reset the block counter and send consecutive frames."""
        self._block_counter = 0
        self._send_consecutive()

    def _end_request(self):
        self._isFinished = True
        self._on_success()

    def send_control_frame(self, flow_status=0, block_size=0, separation_time=0):
        """
        Send a Flow Control (FC) frame.

        Parameters:
            flow_status (int): Flow status:
                               - 0: Continue to send
                               - 1: Wait
                               - 2: Overflow/Abort
            block_size (int): Number of consecutive frames the sender can send before waiting for FC (0 = No limit).
            separation_time (int): Delay between frames (in milliseconds).

        Raises:
            ValueError: If any parameter is out of range or invalid.
        """
        try:
            # Validate inputs
            if flow_status not in [0, 1, 2]:
                # logger.error("Invalid flow status. It must be 0 (Continue), 1 (Wait), or 2 (Overflow/Abort).")
                raise ValueError("Invalid flow status. It must be 0 (Continue), 1 (Wait), or 2 (Overflow/Abort).")
            if not (0 <= block_size <= 255):
                # logger.error("Invalid block size. It must be between 0 and 255.")
                raise ValueError("Invalid block size. It must be between 0 and 255.")
            if not (0 <= separation_time <= 255):
                # logger.error("Invalid separation time. It must be between 0 and 255.")
                raise ValueError("Invalid separation time. It must be between 0 and 255.")

            frame_type = 0x3
            # Construct the FC frame
            first_byte = (frame_type << 4) | flow_status  # Frame type in upper 4 bits, flow status in lower 4 bits
            second_byte = block_size  # Block size as the second byte
            third_byte = separation_time  # Separation time as the third byte

            # Create the FC frame as a bytes object
            control_frame = bytes([first_byte, second_byte, third_byte])

            # Transmit the control frame
            self._txfn(self._address, control_frame)
            # logger.info(f"Sent control frame: {control_frame.hex().upper()}")
            print(f"Sent control frame: {control_frame.hex().upper()}")
            self._end_request()

        except Exception as e:
            # logger.error(f"Error in send_control_frame method: {e}")
            print(f"Error in send_control_frame method: {e}")
            self._on_error(e)

    def get_address(self):
        return self._address
