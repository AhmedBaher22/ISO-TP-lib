import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from can_layer.enums import CANInterface
from can_layer.CanExceptions import CANError
from can_layer.can_communication import CANCommunication, CANConfiguration

 

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


            # Send a message
            success = can_comm.send_message(
                arbitration_id=0x33,
                data=[0, 25, 0, 1, 3, 1, 4, 1],
                timeout=5.0,
                require_ack=False,
                retries=3,
                retry_delay=1.0
            )

            if success:
                print("Message sent successfully")
            else:
                print("Failed to send message")

            # Get bus statistics
            stats = can_comm.get_bus_statistics()
            print(f"Bus Statistics: {stats}")

    except CANError as e:
        print(f"CAN operation failed: {e.message}")

if __name__ == "__main__":
    main()