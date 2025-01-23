import can
import logging
from can.interfaces.vector.exceptions import VectorInitializationError

# Create an error-specific logger
ErrorLogger = logging.getLogger("ErrorLogger")
ErrorLogger.setLevel(logging.ERROR)

# Create a formatter for the ErrorLogger
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

# Create a file handler for the ErrorLogger
error_file_handler = logging.FileHandler("logs/can_receive_errors.log")
error_file_handler.setFormatter(error_formatter)
error_file_handler.setLevel(logging.ERROR)

# Create a console handler for the ErrorLogger
error_console_handler = logging.StreamHandler()
error_console_handler.setFormatter(error_formatter)
error_console_handler.setLevel(logging.ERROR)

# Add both handlers to the ErrorLogger
ErrorLogger.addHandler(error_file_handler)
ErrorLogger.addHandler(error_console_handler)

# Create a general logger for INFO-level logging
logger = logging.getLogger("GeneralLogger")
logger.setLevel(logging.INFO)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

# Create a console handler for general logging
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Create a file handler for general logging
file_handler = logging.FileHandler("logs/can_receiver.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Add handlers to the general logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

fd_flag=False
extended_flag=False
channel_number=0
filterFlashCommand = [{"can_id": 0x33, "can_mask": 0x7FF, "extended": False}]
time_out_in_seconds=10

try:
    # Initialize the CAN bus with the Vector interface
    with can.Bus(interface="vector", channel=channel_number, app_name="UDSwithIsoTp", fd=fd_flag) as bus:
        
        logger.info("CAN bus initialized successfully for receiving messages.")

        while True:

            logger.info("Waiting to receive a CAN message...")
            bus.set_filters(filterFlashCommand)
            # Receive a message
            msg = bus.recv(timeout=time_out_in_seconds)  # Adjust timeout as needed
            if msg:

                logger.info("Message received with arbitration_id=0x%X and data=%s , and hole message = %s", msg.arbitration_id, msg.data, msg)

                # Send acknowledgment
                ack_msg = can.Message(arbitration_id=msg.arbitration_id, data=[1], is_extended_id=extended_flag,is_fd=fd_flag)
                try:
                    bus.send(ack_msg)

                    logger.info("Acknowledgment sent for message arbitration_id=0x%X", msg.arbitration_id)
                except can.CanError as e:
                    ErrorLogger.error("Error: CanError while sending acknowledgment: %s", e)


            else:
                logger.info("Timeout: No message received.")
                break

            

except VectorInitializationError as e:
    ErrorLogger.error("Error: VectorInitializationError: %s, Details: Vector CAN hardware not detected or configured incorrectly. Check connections and drivers.", e)


except ValueError as e:
    ErrorLogger.error("Error: ValueError due to Invalid parameter provided for CAN Bus initialization: %s", e)

except OSError as e:
    ErrorLogger.error("Error: OSError likely due to hardware or system issues: %s", e)


except can.CanError as e:
    ErrorLogger.error("Error: A general CAN-related issue occurred during initialization: %s", e)


except Exception as e:
    ErrorLogger.error("Error: Unexpected exception occurred: %s", e)


finally:
    logger.info("CAN receive operation complete.")
