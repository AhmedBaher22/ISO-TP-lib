from typing import Optional, List, Dict
import sys
import os
from time import sleep
from typing import List
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.IsoTpConfig import IsoTpConfig
from iso_tp_layer.IsoTp import IsoTp
from uds_layer.uds_client import UdsClient
from iso_tp_layer.Address import Address
from can_layer.can_communication import CANCommunication, CANConfiguration
from can_layer.enums import CANInterface
from can_layer.CanExceptions import CANError
from uds_layer.uds_enums import SessionType
from uds_layer.server import Server

def init_uds_client(
    client_id: int = 0x33,
    can_config: Optional[CANConfiguration] = None,
    isotp_config: Optional[IsoTpConfig] = None,
    filters: Optional[List[Dict]] = None
) -> Optional[UdsClient]:
    """
    Initializes the UDS client, ISO-TP layer, and CAN communication layers.
    Allows optional customization of client_id, CANConfiguration, IsoTpConfig, and filters.
    Returns the UdsClient object.

    Args:
        client_id: Optional ID for the UdsClient. Default is 0x33.
        can_config: Optional CANConfiguration object for CAN settings.
        isotp_config: Optional IsoTpConfig object for ISO-TP layer configuration.
        filters: Optional list of CAN filters.
    """
    try:
        # Step 1: Initialize UDS Client
        client = UdsClient(client_id=client_id)

        # Step 2: Configure ISO-TP layer
        if not isotp_config:
            isotp_config = IsoTpConfig(
                max_block_size=8,
                timeout=1000,
                stmin=10,
                on_recv_success=client.receive_message,
                on_recv_error=client.on_fail_receive,
                recv_id=client.get_client_id
            )
        isotp_layer = IsoTp(isotp_config)
        client.set_isotp_send(isotp_layer.send)

        # Step 3: Configure CAN communication
        if not can_config:
            can_config = CANConfiguration(
                interface=CANInterface.VECTOR,
                channel=0,
                app_name="udsWithIsoTp",
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
        return client

    except CANError as e:
        print(f"CAN operation failed: {e.message}")
        return None
