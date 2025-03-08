import threading
import time
from bitarray import bitarray
import sys
import os
import can  # Import python-can library

# Add package directory to system path
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)

# Import ISO-TP related modules
from iso_tp_layer.IsoTpConfig import IsoTpConfig
from iso_tp_layer.frames.SingleFrameMessage import SingleFrameMessage
from iso_tp_layer.frames.FirstFrameMessage import FirstFrameMessage
from iso_tp_layer.frames.ConsecutiveFrameMessage import ConsecutiveFrameMessage
from iso_tp_layer.frames.FlowControlFrameMessage import FlowControlFrameMessage
from iso_tp_layer.frames.FlowStatus import FlowStatus
from iso_tp_layer.IsoTp import IsoTp, message_to_bitarray
from iso_tp_layer.Address import Address
from iso_tp_layer.Exceptions import TimeoutException


# Callback functions
def on_success(data: bitarray, address: Address):
    print(f"UDS on_success:\naddress: {address}\ndata: {data.to01()}")


def on_error(error):
    print(f"Error occurred: {error}")


def can_send(arbitration_id: int, data: bytearray):
    print(f"CAN Send:\narbitration_id: {arbitration_id}\ndata: {data}")


# Create an IsoTpConfig instance
config = IsoTpConfig(
    max_block_size=3,  # Block size for testing flow control
    timeout=0,  # Short timeout for testing
    stmin=0,  # Minimum separation time
    on_recv_success=on_success,
    on_recv_error=on_error,
    recv_id=1
)

# Create an IsoTp instance
iso_tp = IsoTp(config)
iso_tp.set_send_fn(can_send)

# Define CAN address
address = Address(txid=0x123, rxid=0x456)


# Test messages using can.Message
def can_messages():
    """Function to simulate sending CAN messages to the IsoTp layer."""

    # # # 1. **Test Single Frame Message**
    print("\n--- Test: Single Frame ---")
    message_data = bitarray('1010101011100001')  # Example data (16 bits)
    single_frame = SingleFrameMessage(dataLength=len(message_data) // 8, data=message_data)

    # # Create a CAN message
    can_msg = can.Message(arbitration_id=0x123, data=message_to_bitarray(single_frame).tobytes(), is_extended_id=False)
    iso_tp.recv_can_message(can_msg)
    # #
    # # # 2. **Test First Frame Message**
    # print("\n--- Test: First Frame ---")
    # first_frame_data = bitarray('101010101110000110101010111000011010101011100001')  # 48 bits -> 6 bytes
    # first_frame = FirstFrameMessage(dataLength=8, data=first_frame_data)
    #
    # can_msg = can.Message(arbitration_id=0x123, data=message_to_bitarray(first_frame).tobytes(), is_extended_id=False)
    # iso_tp.recv_can_message(can_msg)

    # # # 3. **Test Consecutive Frames (Correct Order)**
    # print("\n--- Test: Consecutive Frames in Order ---")
    # consecutive_frame_1 = ConsecutiveFrameMessage(sequenceNumber=1, data=bitarray('11110000'))  # 8 bits -> 1 byte
    # consecutive_frame_2 = ConsecutiveFrameMessage(sequenceNumber=2, data=bitarray('00001111'))  # 8 bits -> 1 byte
    #
    # can_msg1 = can.Message(arbitration_id=0x123, data=message_to_bitarray(consecutive_frame_1).tobytes(),
    #                        is_extended_id=False)
    # time.sleep(1)
    # can_msg2 = can.Message(arbitration_id=0x123, data=message_to_bitarray(consecutive_frame_2).tobytes(),
    #                        is_extended_id=False)
    #
    # iso_tp.recv_can_message(can_msg1)
    # iso_tp.recv_can_message(can_msg2)
    #
    # time.sleep(1)

    # 4. **Test Consecutive Frame Out of Sequence**
    # print("\n--- Test: Consecutive Frame Out of Sequence ---")
    # first_frame_data = bitarray('101010101110000110101010111000011010101011100001')  # 48 bits -> 6 bytes
    # first_frame = FirstFrameMessage(dataLength=8, data=first_frame_data)
    #
    # can_msg = can.Message(arbitration_id=0x123, data=message_to_bitarray(first_frame).tobytes(), is_extended_id=False)
    # iso_tp.recv_can_message(can_msg)
    #
    # out_of_order_frame = ConsecutiveFrameMessage(sequenceNumber=3, data=bitarray('11001100'))  # Should be 1, not 3
    # can_msg = can.Message(arbitration_id=0x123, data=message_to_bitarray(out_of_order_frame).tobytes(),
    #                       is_extended_id=False)
    # iso_tp.recv_can_message(can_msg)

    print("\nAll test cases executed.")


# Run test
can_messages()

# import threading
# import time
# from bitarray import bitarray
# import sys
# import os
#
# current_dir = os.path.dirname(os.path.abspath(__file__))
# package_dir = os.path.abspath(os.path.join(current_dir, ".."))
# sys.path.append(package_dir)
# from iso_tp_layer.IsoTpConfig import IsoTpConfig
# from iso_tp_layer.frames.SingleFrameMessage import SingleFrameMessage
# from iso_tp_layer.frames.FirstFrameMessage import FirstFrameMessage
# from iso_tp_layer.frames.ConsecutiveFrameMessage import ConsecutiveFrameMessage
# from iso_tp_layer.frames.FlowControlFrameMessage import FlowControlFrameMessage
# from iso_tp_layer.frames.FlowStatus import FlowStatus
# from iso_tp_layer.IsoTp import IsoTp, message_to_bitarray
# from iso_tp_layer.Address import Address
# from iso_tp_layer.Exceptions import TimeoutException
#
#
# # Callback functions
# def on_success(data: bitarray, address: Address):
#     print(f"UDS on_success:\naddress: {address}\ndata: {data.to01()}")
#
#
# def on_error(error):
#     print(f"Error occurred: {error}")
#
#
# def can_send(arbitration_id: int, data: bytearray):
#     print(f"CAN Send:\narbitration_id: {arbitration_id}\ndata: {data}")
#
#
# # Create an IsoTpConfig instance
# config = IsoTpConfig(
#     max_block_size=3,  # Block size for testing flow control
#     timeout=0,  # Short timeout for testing
#     stmin=0,  # Minimum separation time
#     on_recv_success=on_success,
#     on_recv_error=on_error,
#     recv_id=1
# )
#
# # Create an IsoTp instance
# iso_tp = IsoTp(config)
# iso_tp.set_send_fn(can_send)
#
# # Define CAN address
# address = Address(txid=0x123, rxid=0x456)
# print(threading.current_thread())
# # 1. **Test Single Frame Message**
# print("\n--- Test: Single Frame ---")
# message_data = bitarray('1010101011100001')  # Example data (16 bits)
# single_frame = SingleFrameMessage(dataLength=len(message_data) // 8, data=message_data)
# iso_tp.recv(message_to_bitarray(single_frame), address)
#
# # 2. **Test First Frame Message (Initiate Multi-Frame Transmission)**
# print("\n--- Test: First Frame ---")
# first_frame_data = bitarray('101010101110000110101010111000011010101011100001')  # 48 bits -> 6 bytes
# first_frame = FirstFrameMessage(dataLength=8, data=first_frame_data)
# iso_tp.recv(message_to_bitarray(first_frame), address)
#
# # 3. **Test Consecutive Frames (Correct Order)**
# print("\n--- Test: Consecutive Frames in Order ---")
# consecutive_frame_1 = ConsecutiveFrameMessage(sequenceNumber=1, data=bitarray('11110000'))  # 8 bits -> 1 bytes
# consecutive_frame_2 = ConsecutiveFrameMessage(sequenceNumber=2, data=bitarray('00001111'))  # 8 bits -> 1 bytes
# iso_tp.recv(message_to_bitarray(consecutive_frame_1), address)
# iso_tp.recv(message_to_bitarray(consecutive_frame_2), address)
# time.sleep(1)
#
# # 4. **Test Consecutive Frame Out of Sequence**
# print("\n--- Test: Consecutive Frame Out of Sequence ---")
# first_frame_data = bitarray('101010101110000110101010111000011010101011100001')  # 48 bits -> 6 bytes
# first_frame = FirstFrameMessage(dataLength=8, data=first_frame_data)
# iso_tp.recv(message_to_bitarray(first_frame), address)
#
# out_of_order_frame = ConsecutiveFrameMessage(sequenceNumber=2, data=bitarray('11001100'))  # Should be 3, not 5
# iso_tp.recv(message_to_bitarray(out_of_order_frame), address)
#
#
# print("\nAll test cases executed.")
