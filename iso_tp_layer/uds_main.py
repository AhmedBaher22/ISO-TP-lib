from IsoTpConfig import IsoTpConfig
from IsoTp import IsoTp
from uds_client import UdsClient
from Address import Address
from can_communication import CANCommunication, CANConfiguration
from enums import CANInterface
from CanExceptions import CANError
from uds_enums import SessionType

def main():
    # Create UDS Client instance
    client = UdsClient(client_id=0x123)

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
            isotp_layer.set_send_fn(can_comm.send_message)
            



    except CANError as e:
        print(f"CAN operation failed: {e.message}")    
    # Initialize communication with an ECU
    print("\n=== Initializing Communication with ECU ===")
    ecu_address = Address(addressing_mode=0, txid=0x7E8, rxid=0x7E0)
    client.add_server(ecu_address, SessionType.EXTENDED)

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
    # for server in client._servers:
    #     print(f"\nServer ID: {hex(server.can_id)}")
    #     print(f"Session Type: {server.session}")
    #     print(f"P2 Timing: {server.p2_timing}ms")
    #     print(f"P2* Timing: {server.p2_star_timing}ms")
    #     print("Logs:")
    #     for log in server._logs:
    #         print(f"  - {log}")

    # # Clean up
    # print("\n=== Cleaning Up ===")
    # # Add any necessary cleanup code here

if __name__ == "__main__":
    main()