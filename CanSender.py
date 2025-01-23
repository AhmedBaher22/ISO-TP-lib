import can
import logging

# Create an error-specific logger
ErrorLogger = logging.getLogger("ErrorLogger")
ErrorLogger.setLevel(logging.ERROR)

# Create a formatter for the ErrorLogger
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

# Create a file handler for the ErrorLogger
error_file_handler = logging.FileHandler("logs/can_sender_errors.log")
error_file_handler.setFormatter(error_formatter)
error_file_handler.setLevel(logging.ERROR)

# Create a console handler for the ErrorLogger (prints to terminal)
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
file_handler = logging.FileHandler("logs/can_sender.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Add handlers to the general logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

fd_flag=False
extended_flag=False
channel_number=0
message_id = 0x33
retries = 3  # Number of retries
time_out_in_seconds=5

try:
    # Initialize CAN bus
    with can.Bus(interface="vector", channel=channel_number, app_name="udsWithIsoTp",fd=fd_flag) as bus:
        print("CAN bus initialized successfully.")
        logger.info("CAN bus initialized successfully.")
        bus.set_filters([{"can_id": message_id, "can_mask": 0x7FF, "extended": extended_flag}])
        # Message to be sent
        msg = can.Message(arbitration_id=message_id, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=extended_flag,is_fd=fd_flag)

        acknowledgment_received = False


        while not acknowledgment_received and retries > 0:
            try:
                # Send the CAN message
                bus.send(msg)
                print(f"Message sent: {msg}")
                logger.info("Message sent with arbitration_id=0x%X and data=%s", msg.arbitration_id, msg.data)

                # Wait for acknowledgment
                ack = bus.recv(timeout=time_out_in_seconds)  # Wait for acknowledgment
                if ack :  # Acknowledgment message ID
                    print("Acknowledgment received.")
                    logger.info("Acknowledgment received for arbitration_id=0x%X", ack.arbitration_id)
                    acknowledgment_received = True
                else:
                    print("No acknowledgment received. Retrying...")
                    logger.warning("No acknowledgment received. Retrying...")
                    retries -= 1

            except can.CanError as e:
                ErrorLogger.error("CanError while sending a message: %s", e)
                print(f"Error: Failed to send CAN message: {e}")
                retries -= 1

        if not acknowledgment_received:
            print("Message transmission failed after retries.")
            ErrorLogger.error("Message transmission failed after retries.")
            

except can.interfaces.vector.exceptions.VectorInitializationError as e:
    ErrorLogger.error("Error: VectorInitializationError: %s , Details: Vector CAN hardware not detected or configured incorrectly. Check connections and drivers.", e)


except ValueError as e:
    ErrorLogger.error("Error: Invalid parameter provided for CAN Bus initialization: %s", e)
   

except OSError as e:
    ErrorLogger.error("Error: OSError likely due to hardware or system issues: %s", e)


except can.CanError as e:
    ErrorLogger.error("Error: A general CAN-related issue occurred %s", e)


except Exception as e:
    ErrorLogger.error("Error: Unexpected exception occurred: %s", e)


finally:
    logger.info("CAN operation complete.")
