import time
from bitarray import bitarray
import sys
import os
import can
from typing import Optional, List, Dict

current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)

from iso_tp_layer.frames.FirstFrameMessage import FirstFrameMessage
from iso_tp_layer.frames.ConsecutiveFrameMessage import ConsecutiveFrameMessage
from iso_tp_layer.frames.SingleFrameMessage import SingleFrameMessage
from iso_tp_layer.IsoTp import message_to_bitarray
from iso_tp_layer.IsoTpConfig import IsoTpConfig
from iso_tp_layer.IsoTp import IsoTp
from iso_tp_layer.Address import Address
from can_layer.can_communication import CANCommunication, CANConfiguration
from can_layer.enums import CANInterface
from can_layer.CanExceptions import CANError
# from logger import Logger, LogType, ProtocolType
# logger = Logger(ProtocolType.ISO_TP)


def sample_fn(X):
    pass


def on_success(msg: bitarray, address: Address):
    msg = msg.tobytes()
    print(f"UDS on_success:\naddress: {address}\ndata: {msg.hex()}")

    iso_tp = init_isotp_client()

    time = 5
    message = bytearray()
    flg = False
    ack_flag = False
    send_flag = False
    ack_msg = None

    if ack_flag:
        print("Hello")
        ack_flag = False
        memory = msg[4]
        memoryAddress = msg[5]
        memorySize = msg[6]
        # logger.info("Message address = 0x%X and memorySize= 0x%X",
        #             memoryAddress, memorySize)

        ack_msg = [0x71, 0x01, 0xff, 0x00, 0x00]
        time -= 1
        flg = True

    elif msg[0] == 0x10:
        ack_msg = [0x50, 0x03, 0x00, 0x55, 0x01, 0x55]
        time -= 1

    #  read data by identifier
    elif msg[0] == 0x22:
        ack_msg = [0x62, 0x01, 0x90, 0x55]
        time -= 1

    elif msg[0] == 0x11:
        ack_msg = [0x7F, 0x11, 0x12]
        time -= 1

    # write data by indetifier
    elif msg[0] == 0x2E:
        ack_msg = [0x6E, 0x01, 0x90]
        time -= 1

    elif msg[0] == 0x34:
        ack_msg = [0x74, 0x01, 0x02]
        flg = True
        time -= 1

    elif msg[0] == 0x36 and msg[1] == 0x01:
        message.append(msg[2])
        message.append(msg[3])
        ack_msg = [0x76, 0x01]
        time -= 1
        flg = True

    elif msg[0] == 0x36 and msg[1] == 0x02:
        message.append(msg[2])
        message.append(msg[3])
        # logger.info(f"Complete msg received: {message}")
        ack_msg = [0x76, 0x02]
        time -= 1
        flg = True

    elif msg[0] == 0x37:
        ack_msg = [0x77]
        time -= 1
        flg = True

    elif msg[0] == 0x31 and msg[3] == 0x01:
        memory = msg[4]
        memoryAddress = msg[5]
        memorySize = msg[6]
        # logger.info("Message address = 0x%X and memorySize= 0x%X",
        #             memoryAddress, memorySize)
        ack_msg = [0x71, 0x01, 0xFF, 0x01, 0x00]
        time -= 1
        flg = True


    elif msg[0] == 0x31 and msg[3] == 0x00:
        memory = msg[4]
        memoryAddress = msg[5]
        memorySize = msg[6]
        # logger.info("Message address = 0x%X and memorySize= 0x%X",
        #             memoryAddress, memorySize)

        ack_msg = [0x71, 0x01, 0xFF, 0x00, 0x00]
        time -= 1
        flg = True

    elif msg[1] == 0x31 and msg[4] == 0x00:

        memory = msg[4]
        memoryAddress = msg[5]
        memorySize = msg[6]
        # logger.info("Message address = 0x%X and memorySize= 0x%X",
        #             memoryAddress, memorySize)

        # HEREEE!!
        print("LALALA\n\nLALALAL\n\nLALALA\n")
        byte_arr = bytearray([0x30, 0x00, 0x00])

        iso_tp._config.send_fn(arbitration_id=address._txid, data=byte_arr)

        time -= 1
        flg = True
        ack_flag = True

    elif msg[0] == 0x31 and msg[3] == 0x02:

        # logger.info("Message address = 0x%X and memorySize= 0x%X",
        #             memoryAddress, memorySize)
        ack_msg = [0x71, 0x01, 0xFF, 0x02, 0x00]
        time -= 1
        flg = True

    # Send acknowledgment
    try:
        print(f"ack_msg: {ack_msg}")

        # if (msg[0] == 0x03 or msg[0] == 0x02 or msg[1] == 0x11 or flg) and time > 0:
        bit_arr = bitarray()
        for byte in ack_msg:
            bit_arr.extend(f"{byte:08b}")  # Convert to 8-bit binary and append

        iso_tp.send(bit_arr, address, sample_fn, sample_fn)
        print("ack message", ack_msg)
        # logger.info("Acknowledgment sent for message arbitration_id=0x%X", msg.arbitration_id)

    except can.CanError as e:
        # ErrorLogger.error("Error: CanError while sending acknowledgment: %s", e)
        print("Error: CanError while sending acknowledgment: %s", e)


def on_error(error):
    print(f"Error occurred: {error}")

def init_isotp_client(
    client_id: int = 0x33,
    can_config: Optional[CANConfiguration] = None,
    isotp_config: Optional[IsoTpConfig] = None,
    filters: Optional[List[Dict]] = None
) -> Optional[IsoTp]:

    try:
        # Step 2: Configure ISO-TP layer
        if not isotp_config:
            isotp_config = IsoTpConfig(
                max_block_size=8,
                timeout=1000,
                stmin=10,
                on_recv_success=on_success,
                on_recv_error=on_error,
                recv_id=client_id
            )
        isotp_layer = IsoTp(isotp_config)

        # Step 3: Configure CAN communication
        if not can_config:
            can_config = CANConfiguration(
                interface=CANInterface.VECTOR,
                serial_number=100,
                channel=0,
                app_name="UDS",
                fd_flag=False,
                extended_flag=False,
                recv_callback=isotp_layer.recv_can_message
            )
        can_comm = CANCommunication(can_config)

        # Step 4: Set CAN filters
        if not filters:
            filters = [{"can_id": client_id, "can_mask": 0x7FF, "extended": False}]
        can_comm.set_filters(filters)

        # Step 5: Start receiving CAN messages
        can_comm.start_receiving()

        # Step 6: Set send function for ISO-TP layer
        isotp_layer.set_send_fn(can_comm.send_message)

        # Return the initialized UDS client
        return isotp_layer

    except CANError as e:
        print(f"CAN operation failed: {e.message}")
        return None





# Define CAN address
address = Address(txid=0x123, rxid=0x456)
iso_tp = init_isotp_client()


# # # 1. **Test Single Frame Message**
# print("\n--- Test: Single Frame ---")
# message_data = bitarray('1010101011100001')  # Example data (16 bits)
# single_frame = SingleFrameMessage(dataLength=len(message_data) // 8, data=message_data)
#
# # Create a CAN message
# can_msg = can.Message(arbitration_id=0x123, data=message_to_bitarray(single_frame).tobytes(), is_extended_id=False)
# iso_tp.recv_can_message(can_msg)


while True:
    time.sleep(1)
