import time
from bitarray import bitarray
import sys
import os
import can
from typing import Optional, List, Dict

current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)

from iso_tp_layer.IsoTpConfig import IsoTpConfig
from iso_tp_layer.IsoTp import IsoTp
from iso_tp_layer.Address import Address
from can_layer.can_communication import CANCommunication, CANConfiguration
from can_layer.enums import CANInterface
from can_layer.CanExceptions import CANError



def sample_fn(X):
    pass


global_ack_msg: List[List[int]] = []


def on_success(msg: bitarray, address: Address):
    global global_ack_msg
    msg = msg.tobytes()

    for x in global_ack_msg:
        ack_msg_bytes = bytes(x)
        if msg == ack_msg_bytes:
            return



    print(f"UDS on_success:\naddress: {address}\ndata: {msg.hex()}")

    # iso_tp = init_isotp_client(False)

    time = 5
    message = bytearray()
    flg = False
    ack_flag = False
    send_flag = False
    ack_msg = None

    if ack_flag:
        ack_flag = False
        ack_msg = [0x71, 0x01, 0xff, 0x00, 0x00]
        time -= 1
        flg = True

    elif msg[2] == 0x10:
        ack_msg = [0x50, 0x03, 0x00, 0x55, 0x01, 0x55]
        time -= 1

    #  read data by identifier
    elif msg[2] == 0x22:
        ack_msg = [0x62, 0x01, 0x90, 0x55]
        time -= 1

    elif msg[2] == 0x11:
        ack_msg = [0X51, 0x01]
        time -= 1

    # write data by indetifier
    elif msg[2] == 0x2E:
        ack_msg = [0x6E, 0x01, 0x90]
        time -= 1

    elif msg[2] == 0x34:
        ack_msg = [0x74, 0x01, 0x02]
        flg = True
        time -= 1

    elif msg[2] == 0x36 and msg[3] == 0x01:
        message.append(msg[2])
        message.append(msg[3])
        ack_msg = [0x76, 0x01]
        time -= 1
        flg = True

    elif msg[2] == 0x36 and msg[3] == 0x02:
        message.append(msg[2])
        # message.append(msg[3])
        ack_msg = [0x76, 0x02]
        time -= 1
        flg = True


    elif msg[2] == 0x37:
        ack_msg = [0x77]
        time -= 1
        flg = True

    elif msg[2] == 0x31 and msg[5] == 0x01:
        ack_msg = [0x71, 0x01, 0xFF, 0x01, 0x00]
        time -= 1
        flg = True


    elif msg[2] == 0x31 and msg[5] == 0x00:
        ack_msg = [0x71, 0x01, 0xFF, 0x00, 0x00]
        time -= 1
        flg = True

    elif msg[3] == 0x31 and msg[6] == 0x00:
        byte_arr = bytearray([0x30, 0x00, 0x00])
        iso_tp._config.send_fn(arbitration_id=address._txid, data=byte_arr)
        time -= 1
        flg = True
        ack_flag = True

    elif msg[2] == 0x31 and msg[5] == 0x02:
        ack_msg = [0x71, 0x01, 0xFF, 0x02, 0x00]
        time -= 1
        flg = True



    # Send acknowledgment
    try:
        da_msg=[0x00,0x33]
        da_msg.extend(ack_msg)
        print(f"ack_msg: {da_msg}")
        iso_tp.send(da_msg, address, sample_fn, sample_fn)
        print("ack message", da_msg)
        global_ack_msg.append(da_msg)

    except can.CanError as e:
        # ErrorLogger.error("Error: CanError while sending acknowledgment: %s", e)
        print("Error: CanError while sending acknowledgment: %s", e)


def on_error(error):
    print(f"Error occurred: {error}")


def init_isotp_client(
        flag: bool = True,
        client_id: int = 0x55,
        can_config: Optional[CANConfiguration] = None,
        isotp_config: Optional[IsoTpConfig] = None,
        filters: Optional[List[Dict]] = None
) -> Optional[IsoTp]:
    try:
        # Step 2: Configure ISO-TP layer
        if not isotp_config:
            isotp_config = IsoTpConfig(
                max_block_size=0,
                timeout=1000,
                stmin=0,
                on_recv_success=on_success,
                on_recv_error=on_error,
                recv_id=client_id
            )
        isotp_layer = IsoTp(isotp_config)

        # Step 3: Configure CAN communication
        if not can_config:
            can_config = CANConfiguration(
                interface=CANInterface.SOCKETCAN,
                serial_number=100,
                channel=0,
                app_name="can0",
                fd_flag=False,
                extended_flag=False,
                recv_callback=isotp_layer.recv_can_message
            )
        can_comm = CANCommunication(can_config)

        # Step 4: Set CAN filters
        if not filters:
            filters = [{"can_id": 0x123, "can_mask": 0x000, "extended": False}]
        can_comm.set_filters(filters)

        # Step 5: Start receiving CAN messages
        if flag:
            can_comm.start_receiving()

        # Step 6: Set send function for ISO-TP layer
        isotp_layer.set_send_fn(can_comm.send_message)

        # Return the initialized UDS client
        return isotp_layer

    except CANError as e:
        print(f"CAN operation failed: {e.message}")
        return None


# Define CAN address
address = Address(txid=0x33, rxid=0x123)
iso_tp = init_isotp_client()

while True:
    time.sleep(1)