# class CAN_ISO_TP:
#     def __init__(self, rxfn):
#         """
#         Initializes the CAN-ISO-TP instance.

#         :param rxfn: A callable function that returns an 8-byte frame when called.
#         """
#         self.rxfn = rxfn

#     def receive(self):
#         """
#         Receives a message using the ISO-TP protocol.

#         :return: The concatenated payload of the message.
#         :raises ValueError: If there is a sequence number mismatch.
#         """
#         # Call rxfn to receive the first frame
#         first_frame = self.rxfn()
#         if len(first_frame) != 8:
#             raise ValueError("Invalid frame length: Frame must be 8 bytes.")

#         frame_type = first_frame[0] >> 4  # Extract the first 4 bits to determine the frame type

#         if frame_type == 0x0:  # Single Frame
#             data_length = first_frame[0] & 0x0F  # Extract the next 4 bits for data length
#             if data_length > 7:
#                 raise ValueError("Invalid data length for single frame.")

#             return first_frame[1:1 + data_length]

#         elif frame_type == 0x1:  # First Frame
#             # Extract the message length (12 bits)
#             message_length = ((first_frame[0] & 0x0F) << 8) | first_frame[1]
#             if message_length == 0 or message_length > 4095:
#                 raise ValueError("Invalid message length for first frame.")

#             # Collect the initial 6 bytes of the message
#             payload = bytearray(first_frame[2:])

#             # Sequence number starts at 0
#             expected_sequence_number = 0

#             # Receive consecutive frames until the message is complete
#             while len(payload) < message_length:
#                 consecutive_frame = self.rxfn()
#                 if len(consecutive_frame) != 8:
#                     raise ValueError("Invalid frame length: Frame must be 8 bytes.")

#                 cf_type = consecutive_frame[0] >> 4
#                 if cf_type != 0x2:  # Verify this is a consecutive frame
#                     raise ValueError("Invalid frame type: Expected consecutive frame.")

#                 sequence_number = consecutive_frame[0] & 0x0F  # Extract sequence number
#                 if sequence_number != expected_sequence_number:
#                     raise ValueError(f"Sequence number mismatch: Expected {expected_sequence_number}, got {sequence_number}.")

#                 # Append the data from this frame
#                 payload.extend(consecutive_frame[1:])

#                 # Update the expected sequence number (rollover after 0xF)
#                 expected_sequence_number = (expected_sequence_number + 1) % 0x10

#             # Trim any extra bytes in the last frame if the payload exceeds the message length
#             return payload[:message_length]

#         else:
#             raise ValueError(f"Invalid frame type: {frame_type}.")

# # Example usage
# if __name__ == "__main__":
#     import itertools

#     def mock_rxfn():
#         """Mock function to simulate receiving CAN frames."""
#         frames = [
#             bytes([0x10, 0x14, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66]),  # First Frame (message length = 0xFFF)
#             bytes([0x20, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD]),  # Consecutive Frame (sequence 0)
#             bytes([0x21, 0xEE, 0xFF, 0x00, 0x11, 0x22, 0x33, 0x44]),  # Consecutive Frame (sequence 1)
#         ]
#         return itertools.cycle(frames)

#     # Instantiate the CAN_ISO_TP class
#     receiver = CAN_ISO_TP(mock_rxfn().__next__)
    
#     # Receive a message
#     try:
#         message = receiver.receive()
#         print("Received message:", message)
#     except ValueError as e:
#         print("Error:", e)
