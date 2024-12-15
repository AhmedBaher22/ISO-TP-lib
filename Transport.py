from typing import Callable
from Address import Address


class Transport:
    def __init__(self, address: Address, txfn: Callable, rxfn: Callable, tx_padding=0xFF, tx_data_length=8, stmin=0,
                 blocksize=0):
        """
        Initialize the Transport Layer with address, transmit, and receive functions.
        """
        self.address = address
        self.tx_padding = tx_padding  # Default padding value
        self.tx_data_length = tx_data_length  # Default data length for CAN frames
        self.stmin = stmin  # Default separation time (ms)
        self.blocksize = blocksize  # No block size limit by default
        self.txfn = txfn
        self.rxfn = rxfn


    def send(self, data: int):
        """Send data in hexadecimal format using ISO-TP protocol."""
        try:
            # Ensure input is a valid integer
            if not isinstance(data, int):
                raise TypeError("Input data must be an integer representing a hexadecimal value.")

            # Convert the integer to bytes
            try:
                hex_string = f"{data:X}"  # Convert to uppercase hexadecimal string without the '0x' prefix
                if len(hex_string) % 2 != 0:
                    hex_string = "0" + hex_string  # Pad with a leading zero if the length is odd

                byte_data = bytes.fromhex(hex_string)
                print(type(byte_data))
            except ValueError as e:
                raise ValueError(f"Invalid hexadecimal value: {data}. Error: {e}")

            # Determine the frame type based on the length of the byte data
            if len(byte_data) <= 7:
                self._send_single(byte_data)
            else:
                self._send_first(byte_data)

        except Exception as e:
            print(f"Error in send method: {e}")
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

        # Transmit the first frame
        self.txfn(hex_frame)

        # Call _send_consecutive for the rest of the data
        remaining_data = data[6:]  # Data after the first 6 bytes
        if remaining_data:
            self._send_consecutive(remaining_data)

    def _send_consecutive(self, data: bytes):
        """Send consecutive frames of a multi-frame message."""
        index = 0
        sequence_num = 0  # Start sequence number from 0
        while index < len(data):
            first_byte = (0x2 << 4) | (sequence_num & 0x0F)  # 4 MSBs = 0x2, next 4 bits = sequence number
            frame = bytes([first_byte]) + data[index:index + 7].ljust(7, self.tx_padding.to_bytes(1, 'little'))
            hex_frame = frame.hex()  # Convert to hex
            print(f"Consecutive frame (hex): {hex_frame}")
            self.txfn(hex_frame)
            index += 7
            sequence_num = (sequence_num + 1) % 16

    def _send_single(self, data: bytes):
        """Send a single frame message."""
        # Calculate the first byte: 4 MSBs = 0x0, 4 LSBs = length of data
        first_byte = (0x0 << 4) | (len(data) & 0x0F)  # 4 MSBs = 0x0

        # Prepend the first byte to the frame
        frame = bytes([first_byte]) + data.ljust(7, self.tx_padding.to_bytes(1, 'little'))

        # Convert frame to hex for output
        hex_frame = frame.hex()
        print(f"Single frame (hex): {hex_frame}")

        # Transmit the frame
        self.txfn(hex_frame)

    def recv(self):
        """
        Receive a message using the callable function `rxfn` and interpret its bytes based on the frame type.
        """
        try:
            # Receive raw data
            raw_data = self.rxfn()
            if not raw_data:
                raise ValueError("No data received.")

            # Ensure raw_data is in bytes format
            if not isinstance(raw_data, bytes):
                raise TypeError("Received data must be in bytes format.")

            # Get the first byte
            first_byte = raw_data[0]
            first_4_bits = (first_byte >> 4) & 0xF  # Most significant 4 bits

            if first_4_bits == 0x0:  # Single frame
                # Extract the data length from the next 4 bits
                data_length = first_byte & 0xF
                if data_length == 0:
                    raise ValueError("Invalid single-frame data length: 0.")

                # Return only the data of the specified length
                return raw_data[1:1 + data_length]

            elif first_4_bits == 0x1:  # First frame of a multi-frame message
                # Extract the total message length from the next 12 bits
                total_length = ((first_byte & 0xF) << 8) | raw_data[1]
                if total_length == 0:
                    raise ValueError("Invalid first-frame data length: 0.")

                # Initialize a buffer to store the full message
                full_message = raw_data[2:]  # Start with the data from this frame

                # Loop to receive consecutive frames until the message is complete
                while len(full_message) < total_length:
                    next_frame = self.rxfn()
                    if not next_frame or len(next_frame) < 1:
                        raise ValueError("Invalid or incomplete consecutive frame received.")

                    # Extract the consecutive frame data (ignore header byte)
                    full_message += next_frame[1:]

                # Return the message up to the total length
                return full_message[:total_length]

            else:
                raise ValueError(f"Unknown frame type: 0x{first_4_bits:X}")

        except Exception as e:
            print(f"Error in recv method: {e}")
            raise
