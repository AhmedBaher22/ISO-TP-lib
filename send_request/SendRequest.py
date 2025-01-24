from typing import Callable
import threading
import time
from bitarray import bitarray
from frames.FlowControlFrameMessage import FlowControlFrameMessage
from frames.FlowStatus import FlowStatus


class SendRequest:
    def __init__(self, txfn: Callable, rxfn: Callable, tx_padding=0xFF):
        self.tx_padding = tx_padding  # Default padding value
        self.txfn = txfn
        self.rxfn = rxfn


    def send(self, data: bitarray):

        # Calculate the number of bytes in the bitarray
        byte_length = len(data) // 8 + (1 if len(data) % 8 != 0 else 0)

        # Determine the frame type based on the length of the byte data
        if byte_length <= 7:
            self._send_single(data.tobytes())
        else:
            self._send_first(data.tobytes())

    def listen_for_control_frame(self, data: bytes):
        """
        Thread function to listen for control frames.
        """
        while True:
            control_frame = self.rxfn()
            if not control_frame:
                # No valid control frame received; keep listening.
                print("Still waiting for a valid control frame...")
                time.sleep(0.1)  # Prevent busy waiting
                continue

            flow_status = FlowStatus(control_frame[0] & 0x0F)
            block_size = control_frame[1]
            stmin = control_frame[2]
            # flowControlFrame = FlowControlFrameMessage(blockSize=block_size, separationTime=stmin, flowStatus=flow_status)


            if flow_status == FlowStatus.Continue:  # Continue to send
                # logger.info("Flow status: Continue to send.")
                print("Flow status: Continue to send.")
                remaining_data = data[6:]  # Data after the first 6 bytes
                if remaining_data:
                    self._send_consecutive(remaining_data)

            elif flow_status == FlowStatus.Wait:  # Wait
                # logger.info("Flow status: Wait.")
                print("Flow status: Wait.")
                while True:
                    time.sleep(self.stmin / 1000.0)
                    control_frame = self.rxfn()
                    flow_status = control_frame[0] & 0x0F

                    if control_frame and flow_status == FlowStatus.Continue:
                        # logger.info("Received continue signal. Resuming...")
                        print("Received continue signal. Resuming...")
                        remaining_data = data[6:]
                        if remaining_data:
                            self._send_consecutive(remaining_data)
                        break
                    elif flow_status == FlowStatus.Abort:
                        # logger.error("Flow status: Abort received. Transmission terminated.")
                        raise ValueError("Flow status: Abort received. Transmission terminated.")
                    else:
                        # logger.info("Still waiting for continue signal...")
                        print("Still waiting for continue signal...")
            elif flow_status == FlowStatus.Abort:  # Abort
                # logger.error("Flow status: Abort received. Transmission terminated.")
                raise ValueError("Flow status: Abort received. Transmission terminated.")
            else:
                # logger.error(f"Unknown flow status: {flow_status}.")
                raise ValueError(f"Unknown flow status: {flow_status}.")

    def _send_first(self, data: bytes):
        """
        Send the first frame of a multi-frame message.
        The first frame includes:
        - 4 MSBs set to 0x1
        - 12 bits for the message length
        - The next 6 bytes of the message data
        """
        # Calculate the total message length
        message_length = len(data)
        if message_length > 4095:  # 12 bits can hold values up to 4095
            # logger.error("Message length exceeds the maximum limit of 4095 bytes for ISO-TP.")
            raise ValueError("Message length exceeds the maximum limit of 4095 bytes for ISO-TP.")

        # Construct the first byte
        first_byte = (0x1 << 4) | ((message_length >> 8) & 0x0F)  # 4 MSBs = 0x1, next 4 bits = upper 4 bits of length

        # Construct the second byte (lower 8 bits of the length)
        second_byte = message_length & 0xFF

        # Include the next 6 bytes of the message (or pad if less than 6 bytes)
        first_frame_data = data[:6]

        # Combine the header and the 6 bytes of message data
        frame = bytes([first_byte, second_byte]) + first_frame_data

        # Convert frame to hex for output
        hex_frame = frame.hex()
        print(f"First frame (hex): {hex_frame}")
        # logger.info(f"First frame (hex): {hex_frame}")



        # Transmit the first frame
        self.txfn(hex_frame)

        listener_thread = threading.Thread(target=self.listen_for_control_frame, args=data, daemon=True)
        listener_thread.start()


    def _send_consecutive(self, data: bytes):
        """
        Send consecutive frames of a multi-frame message, respecting block size and stmin.
        """
        index = 0
        sequence_num = 0
        block_counter = 0

        while index < len(data):
            # Check if block size limit is reached
            if 0 < self.block_size <= block_counter:
                # logger.info(f"Block size limit reached. Waiting for next control frame...")
                print(f"Block size limit reached. Waiting for next control frame...")
                control_frame = self.rxfn()
                print(control_frame)
                if not control_frame:
                    # logger.error("Invalid or missing control frame received.")
                    raise ValueError("Invalid or missing control frame received.")

                flow_status = control_frame[0] & 0x0F
                self.block_size = control_frame[1]
                self.stmin = control_frame[2]

                if flow_status == 0:  # Continue to send
                    # logger.info("Flow status: Continue to send.")
                    print("Flow status: Continue to send.")
                    block_counter = 0
                elif flow_status == 1:  # Wait
                    # logger.info("Flow status: Wait. Waiting for continue signal...")
                    print("Flow status: Wait. Waiting for continue signal...")
                    continue
                elif flow_status == 2:  # Abort
                    # logger.error("Flow status: Abort received. Transmission terminated.")
                    raise ValueError("Flow status: Abort received. Transmission terminated.")
                else:
                    # logger.error(f"Unknown flow status: {flow_status}.")
                    raise ValueError(f"Unknown flow status: {flow_status}.")

            first_byte = (0x2 << 4) | (sequence_num & 0x0F)
            frame = bytes([first_byte]) + data[index:index + 7].ljust(7, self.tx_padding.to_bytes(1, 'little'))
            hex_frame = frame.hex()
            # logger.info(f"Consecutive frame (hex): {hex_frame}")
            print(f"Consecutive frame (hex): {hex_frame}")
            self.txfn(hex_frame)

            index += 7
            sequence_num = (sequence_num + 1) % 16
            block_counter += 1

            # Wait for stmin time if specified
            if self.stmin > 0:
                import time
                time.sleep(self.stmin / 1000.0)

    def _send_single(self, data: bytes):
        """Send a single frame message."""
        # Calculate the first byte: 4 MSBs = 0x0, 4 LSBs = length of data
        first_byte = (0x0 << 4) | (len(data) & 0x0F)  # 4 MSBs = 0x0

        # Prepend the first byte to the frame
        frame = bytes([first_byte]) + data.ljust(7, self.tx_padding.to_bytes(1, 'little'))

        # Convert frame to hex for output
        hex_frame = frame.hex()
        # logger.info(f"Single frame (hex): {hex_frame}")
        print(f"Single frame (hex): {hex_frame}")




        # Transmit the frame
        self.txfn(hex_frame)




    def _send_control_frame(self, flow_status=0, block_size=0, separation_time=0):
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
            self.txfn(control_frame)
            # logger.info(f"Sent control frame: {control_frame.hex().upper()}")
            print(f"Sent control frame: {control_frame.hex().upper()}")

        except Exception as e:
            # logger.error(f"Error in send_control_frame method: {e}")
            print(f"Error in send_control_frame method: {e}")
            raise


