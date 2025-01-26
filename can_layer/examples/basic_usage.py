import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import CANConfig, CANMessage, CANFilter
from src.enums import (
    CANInterface, 
    CANBaudRate, 
    CANMode, 
    CANFrameFormat
)
from src.exceptions import CANError  # Add this import
from src.can_communication import CANCommunication

def message_callback(msg: CANMessage):
    print(f"Received message: ID=0x{msg.arbitration_id:X}, Data={msg._data.hex()}")

def error_callback(error: Exception):
    print(f"Error occurred: {error}")

def main():
    try:
        # Create configuration
        config = CANConfig(
            interface=CANInterface.VECTOR,
            channel=0,
            app_name="udsWithIsoTp",
            baud_rate=CANBaudRate.RATE_500K,
            frame_format=CANFrameFormat.STANDARD,
            mode=CANMode.NORMAL
        )

        # Use as context manager
        with CANCommunication(config) as can_comm:
            # Register callbacks
            can_comm.register_callback(0x123, message_callback)
            can_comm.register_error_callback(error_callback)

            # Send message
            msg = CANMessage(
                arbitration_id=0x123, 
                data=bytes([0x01, 0x02, 0x03]),
                timestamp=time.time()
            )
            can_comm.send_message_async(msg)
            
            # Receive message
            received_msg = can_comm.receive_message(timeout=1.0)
            if received_msg:
                print(f"Received: {received_msg}")
            
            # Get statistics
            stats = can_comm.get_statistics()
            print(f"Statistics: {stats}")

    except CANError as e:
        print(f"CAN Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()