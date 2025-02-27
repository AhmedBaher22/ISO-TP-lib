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


def main():
    # Create UDS Client instance
    client = UdsClient(client_id=0x33)

    # Create an IsoTpConfig instance
    config = IsoTpConfig(
        max_block_size=8,
        timeout=1000,
        stmin=10,
        on_recv_success=client.receive_message,
        on_recv_error=client.on_fail_receive,
        recv_id=client.get_client_id
    )

    # Create ISO-TP layer instance
    isotp_layer = IsoTp(config)
    client.set_isotp_send(isotp_layer.send)
    try:
        # Create configuration
        config = CANConfiguration(
            interface=CANInterface.VECTOR,
            channel=0,
            app_name="udsWithIsoTp",
            fd_flag=False,
            extended_flag=False,
            recv_callback=isotp_layer.recv_can_message
        )

        # Initialize CAN communication
        with CANCommunication(config) as can_comm:
            # Set filters
            filters = [{"can_id": 0x33, "can_mask": 0x7FF, "extended": False}]
            can_comm.set_filters(filters)
            can_comm.start_receiving()
            isotp_layer.set_send_fn(can_comm.send_message)




    except CANError as e:
        print(f"CAN operation failed: {e.message}")


    #opening session control 
    # Initialize communication with an ECU
    print("\n=== Initializing Communication with ECU ===")
    ecu_address = Address(addressing_mode=0, txid=0x33, rxid=0x33)
    client.add_server(ecu_address, SessionType.EXTENDED)
    servers: List[Server] = client.get_servers()
    sleep(1)

    #sending read data by identifier request
    message=servers[0].read_data_by_identifier(vin=[0x01,0x90])
    client.send_message(servers[0].can_id,message)

    #sending ecu reset request
    message=servers[0].ecu_reset(reset_type=0x01)
    client.send_message(servers[0].can_id,message)
    
    #sending write data by intentifier request
    message=servers[0].write_data_by_identifier(vin=[0x01,0x90],data=[0x55,0x26])
    client.send_message(servers[0].can_id,message)


    while True:
        sleep(1)


    # # Wait for session establishment
    # time.sleep(1)

    # # Get the server if it's established
    # server = next((s for s in client._servers if s.can_id == 0x7E8), None)
    # if server:
    #     # Read VIN
    #     print("\n=== Reading VIN ===")
    #     message = server.read_data_by_identifier("VIN")
    #     client.send_message(server.can_id, message)
    #     time.sleep(0.5)

    #     # Write Data
    #     print("\n=== Writing Data ===")
    #     data_to_write = [0x31, 0x32, 0x33, 0x34, 0x35]
    #     message = server.write_data_by_identifier("VIN", data_to_write)
    #     client.send_message(server.can_id, message)
    #     time.sleep(0.5)

    #     # ECU Reset
    #     print("\n=== Performing ECU Reset ===")
    #     reset_type = 0x01  # Hard Reset
    #     message = server.ecu_reset(reset_type)
    #     client.send_message(server.can_id, message)
    #     time.sleep(0.5)

    # # Print final status
    # print("\n=== Final Status ===")
    # print(f"Number of servers: {len(client._servers)}")


    # # Clean up
    # print("\n=== Cleaning Up ===")
    # # Add any necessary cleanup code here


if __name__ == "__main__":
    main()
