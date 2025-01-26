from can_communication import CANCommunication, CANConfiguration
from enums import CANInterface
from exceptions import CANError
 

def hello(message):
    pass


def main():
    try:
        # Create configuration
        config = CANConfiguration(
            interface=CANInterface.VECTOR,
            channel=0,
            app_name="udsWithIsoTp",
            fd_flag=False,
            extended_flag=False,
            recv_callback=hello
        )

        # Initialize CAN communication
        with CANCommunication(config) as can_comm:
            # Set filters
            filters = [{"can_id": 0x33, "can_mask": 0x7FF, "extended": False}]
            can_comm.set_filters(filters)

            can_comm.receive_message(600)

            # Get bus statistics
            stats = can_comm.get_bus_statistics()
            print(f"Bus Statistics: {stats}")

    except CANError as e:
        print(f"CAN operation failed: {e.message}")

if __name__ == "__main__":
    main()