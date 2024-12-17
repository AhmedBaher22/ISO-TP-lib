from typing import Callable
from Address import Address
import logging

ErrorLogger = logging.getLogger("ErrorLogger")
ErrorLogger.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
error_file_handler = logging.FileHandler("logs/isotp.log")
error_file_handler.setFormatter(error_formatter)
error_file_handler.setLevel(logging.ERROR)
error_console_handler = logging.StreamHandler()
error_console_handler.setFormatter(error_formatter)
error_console_handler.setLevel(logging.ERROR)
ErrorLogger.addHandler(error_file_handler)
ErrorLogger.addHandler(error_console_handler)

logger = logging.getLogger("GeneralLogger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler("logs/isotp.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
# class AddressingMode(Enum):
#     Normal_11bits = 0  # Standard 11-bit CAN identifier
#     Extended_29bits = 1  # Extended 29-bit CAN identifier

# class AddressingMode(Enum):
#     Normal_11bits = 0  # Standard 11-bit CAN identifier
#     Extended_29bits = 1  # Extended 29-bit CAN identifier
class Transport:
    def __init__(self, address: Address, txfn: Callable, rxfn: Callable, tx_padding=0xFF, tx_data_length=8, stmin=0,
                 block_size=0,fd=False):
        """
        Initialize the Transport Layer with address, transmit, and receive functions.
        """
        logger.info("transport layer ISO-Tp initialized.")
        self.address = address
        self.tx_padding = tx_padding  # Default padding value
        self.tx_data_length = tx_data_length  # Default data length for CAN frames
        self.stmin = stmin  # Default separation time (ms)
        self.block_size = block_size  # No block size limit by default
        self.txfn = txfn
        self.rxfn = rxfn
        self.fd=fd

    def send(self, data: int):
        """Send data in hexadecimal format using ISO-TP protocol."""
        try:
            # Ensure input is a valid integer
            if not isinstance(data, int):
                logger.error("Input data must be an integer representing a hexadecimal value.")
                raise TypeError("Input data must be an integer representing a hexadecimal value.")

            # Convert the integer to bytes
            try:
                hex_string = f"{data:X}"  # Convert to uppercase hexadecimal string without the '0x' prefix
                if len(hex_string) % 2 != 0:
                    hex_string = "0" + hex_string  # Pad with a leading zero if the length is odd

                byte_data = bytes.fromhex(hex_string)
            except ValueError as e:
                logger.error(f"Invalid hexadecimal value: {data}. Error: {e}")
                raise ValueError(f"Invalid hexadecimal value: {data}. Error: {e}")

            # Determine the frame type based on the length of the byte data
            if len(byte_data) <= 7:
                self._send_single(byte_data)
            else:
                self._send_first(byte_data)

        except Exception as e:
            print(f"Error in send method: {e}")
            logger.error(f"Error in send method: {e}")
            raise

    def _send_first(self, data: bytes):
        """
        Send the first frame of a multi-frame message.
        The first frame includes:
        - 4 MSBs set to 0x1
        - 12 bits for the message length
        - The next 6 bytes of the message data
        """
        # Calculate the total message lefngth
        message_length = len(data)
        if message_length > 4095:  # 12 bits can hold values up to 4095
            logger.error("Message length exceeds the maximum limit of 4095 bytes for ISO-TP.")
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
        logger.info(f"First frame (hex): {hex_frame}")
        # Transmit the first frame
        self.txfn(hex_frame)

        # RECEIVE CONTROL FRAME HERE
        control_frame = self.rxfn()

        if not control_frame :
            logger.error("Invalid or missing control frame received.")
            raise ValueError("Invalid or missing control frame received.")
        
        
        flow_status = control_frame[0] & 0x0F
 
        self.block_size = control_frame[1]
        self.stmin = control_frame[2]

        if flow_status == 0:  # Continue to send
            logger.info("Flow status: Continue to send.")
            print("Flow status: Continue to send.")
            remaining_data = data[6:]  # Data after the first 6 bytes
            if remaining_data:
                self._send_consecutive(remaining_data)
        elif flow_status == 1:  # Wait
            logger.info("Flow status: Wait.")
            print("Flow status: Wait.")
            while True:
                control_frame = self.rxfn()
                
                if control_frame and (control_frame[0] & 0x0F) == 0:
                    logger.info("Received continue signal. Resuming...")
                    print("Received continue signal. Resuming...")
                    remaining_data = data[6:]
                    if remaining_data:
                        self._send_consecutive(remaining_data)
                    break
                else:
                    logger.info("Still waiting for continue signal...")
                    print("Still waiting for continue signal...")
        elif flow_status == 2:  # Abort
            logger.error("Flow status: Abort received. Transmission terminated.")
            raise ValueError("Flow status: Abort received. Transmission terminated.")
        else:
            logger.error(f"Unknown flow status: {flow_status}.")
            raise ValueError(f"Unknown flow status: {flow_status}.")


    def _send_consecutive(self, data: bytes):
        """
        Send consecutive frames of a multi-frame message, respecting block size and stmin.
        """
        index = 0
        sequence_num = 0
        block_counter = 0

        while index < len(data):
            # Check if block size limit is reached
            if self.block_size > 0 and block_counter >= self.block_size:
                logger.info(f"Block size limit reached. Waiting for next control frame...")
                print(f"Block size limit reached. Waiting for next control frame...")
                control_frame = self.rxfn()
                print(control_frame)
                if not control_frame :
                    logger.error("Invalid or missing control frame received.")
                    raise ValueError("Invalid or missing control frame received.")
                
                flow_status = control_frame[0] & 0x0F
                self.block_size = control_frame[1]
                self.stmin = control_frame[2]

                if flow_status == 0:  # Continue to send
                    logger.info("Flow status: Continue to send.")
                    print("Flow status: Continue to send.")
                    block_counter = 0
                elif flow_status == 1:  # Wait
                    logger.info("Flow status: Wait. Waiting for continue signal...")
                    print("Flow status: Wait. Waiting for continue signal...")
                    continue
                elif flow_status == 2:  # Abort
                    logger.error("Flow status: Abort received. Transmission terminated.")
                    raise ValueError("Flow status: Abort received. Transmission terminated.")
                else:
                    logger.error(f"Unknown flow status: {flow_status}.")
                    raise ValueError(f"Unknown flow status: {flow_status}.")

            first_byte = (0x2 << 4) | (sequence_num & 0x0F)
            frame = bytes([first_byte]) + data[index:index + 7].ljust(7, self.tx_padding.to_bytes(1, 'little'))
            hex_frame = frame.hex()
            logger.info(f"Consecutive frame (hex): {hex_frame}")
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
        logger.info(f"Single frame (hex): {hex_frame}")
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
                logger.error("Invalid flow status. It must be 0 (Continue), 1 (Wait), or 2 (Overflow/Abort).")
                raise ValueError("Invalid flow status. It must be 0 (Continue), 1 (Wait), or 2 (Overflow/Abort).")
            if not (0 <= block_size <= 255):
                logger.error("Invalid block size. It must be between 0 and 255.")
                raise ValueError("Invalid block size. It must be between 0 and 255.")
            if not (0 <= separation_time <= 255):
                logger.error("Invalid separation time. It must be between 0 and 255.")
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
            logger.info(f"Sent control frame: {control_frame.hex().upper()}")
            print(f"Sent control frame: {control_frame.hex().upper()}")

        except Exception as e:
            logger.error(f"Error in send_control_frame method: {e}")
            print(f"Error in send_control_frame method: {e}")
            raise

    def recv(self):
        """
        Receive a message using the callable function `rxfn` and interpret its bytes based on the frame type.
        """
        try:
            # Receive raw data
            raw_data = self.rxfn()
            if not raw_data:
                raise ValueError("No data received.")
            
            #check the length of the length of frame
            if not self.fd:
                if len(raw_data) != 8:
                    logger.error("Invalid frame length: Frame must be 8 bytes.")
                    raise ValueError("Invalid frame length: Frame must be 8 bytes.")
            else:
                if len(raw_data) != 64:
                    logger.error("Invalid frame length: Frame must be 64 bytes for FD.")
                    raise ValueError("Invalid frame length: Frame must be 64 bytes for FD.")   
                                        
            # Ensure raw_data is in bytes format
            if not isinstance(raw_data, bytes):
                logger.error("Received data must be in bytes format.")
                raise TypeError("Received data must be in bytes format.")

            frame_type = self._get_frame_type(raw_data)

            if frame_type == 0x0:  # Single frame
                return self._recv_single(raw_data)

            elif frame_type == 0x1:  # First frame of a multi-frame message
                return self._recv_first(raw_data)
            elif frame_type == 0x2:
                logger.error(f"Error: Consecutive Frame received before First Frame")
                raise ValueError(f"Error: Consecutive Frame received before First Frame")
            elif frame_type == 0x3:
                logger.error(f"Error: Received control flow Frame {raw_data[:2]} withot first frame")
                # Handle receive control frame
                raise ValueError(f"Error: Received control flow Frame {raw_data[:2]} withot first frame")
            else:
                logger.error(f"Unknown frame type: 0x{frame_type:X}")
                raise ValueError(f"Unknown frame type: 0x{frame_type:X}")

        except Exception as e:
            logger.error(f"Error in recv method: {e}")
            print(f"Error in recv method: {e}")
            raise


    def _recv_single(self, raw_data):
        first_byte = raw_data[0]
        # Extract the data length from the next 4 bits
        data_length = first_byte & 0xF
        if data_length == 0:
            raise ValueError("Invalid single-frame data length: 0.")

        # Return only the data of the specified length
        return raw_data[1:1 + data_length]

    def _recv_first(self, raw_data):
        first_byte = raw_data[0]
        # Extract the total message length from the next 12 bits
        total_length = ((first_byte & 0xF) << 8) | raw_data[1]
        if total_length == 0:
            raise ValueError("Invalid first-frame data length: 0.")

        self._send_control_frame()

        # Initialize a buffer to store the full message
        full_message = raw_data[2:]  # Start with the data from this frame

        full_message = self._recv_consecutive(full_message=full_message, total_length=total_length)

        # Return the message up to the total length
        return full_message[:total_length]

    def _recv_consecutive(self, full_message, total_length):
        """
        Receive consecutive frames, send control frames at block intervals, and handle errors.
        """
        seq_number = 0
        block_counter = 0

        while len(full_message) < total_length:
            next_frame = self.rxfn()
            if not next_frame:
                raise ValueError(f"Message with expected sequence number: {seq_number} not received.")

            frame_type = self._get_frame_type(next_frame)
            if frame_type != 0x2:
                self._send_control_frame(flow_status=2)  # Abort
                raise ValueError("Invalid frame type: Expected consecutive frame.")

            first_byte = next_frame[0]
            new_seq_number = first_byte & 0x0F

            if seq_number != new_seq_number:
                self._send_control_frame(flow_status=2)  # Abort
                raise ValueError(f"Unexpected sequence number. Expected: {seq_number}, received: {new_seq_number}")

            seq_number = (seq_number + 1) % 16
            full_message += next_frame[1:]

            block_counter += 1
            if self.block_size > 0 and block_counter >= self.block_size:
                self._send_control_frame(flow_status=0)  # Continue
                block_counter = 0

            # Wait for stmin if specified
            if self.stmin > 0:
                import time
                time.sleep(self.stmin / 1000.0)

        return full_message[:total_length]

    def _get_frame_type(self, raw_data):
        # Get the first byte
        first_byte = raw_data[0]
        first_4_bits = (first_byte >> 4) & 0xF  # Most significant 4 bits
        return first_4_bits


    # def set_control_frame_variables: