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
    with can.Bus(interface="vector", channel=channel_number, app_name="UDS", fd=fd_flag) as bus:
        
        logger.info("CAN bus initialized successfully for receiving messages.")
        s = True
        while True:
            logger.info("Waiting to receive a CAN message...")
            bus.set_filters(filterFlashCommand)
            # Receive a message
            time = 5
            message = bytearray()
            msg = bus.recv(timeout=None)  # Adjust timeout as needed
            flg = False
            if msg:
                send_flag = False
                logger.info("Message received with arbitration_id=0x%X and data=%s , and hole message = %s", msg.arbitration_id, msg.data, msg)
                if msg.data[0] == 0x02 and msg.data[1]==0x10:
                    ack_msg = can.Message(arbitration_id=0x33, data=[0x06,0x50,0x03,0x00,0x55,0x01,0x55], is_extended_id=extended_flag,is_fd=fd_flag)
 
                    time -= 1
                #  read data by identifier
                elif msg.data[0] == 0x03 and msg.data[1]==0x22:
                    ack_msg = can.Message(arbitration_id=0x33, data=[0x04,0x62,0x01,0x90,0x55], is_extended_id=extended_flag,is_fd=fd_flag)
                    time -= 1
                elif msg.data[1] == 0x11:
                    ack_msg = can.Message(arbitration_id=0x33, data=[0x03,0x7F,0x11,0x12], is_extended_id=extended_flag,is_fd=fd_flag)
                    time -= 1
                # write data by indetifier
                elif msg.data[1] == 0x2E:
                    ack_msg = can.Message(arbitration_id=0x33, data=[0x03,0x6E,0x01,0x90], is_extended_id=extended_flag,is_fd=fd_flag)
                    time -= 1

                elif msg.data[1] == 0x34:
                    print("Hello")
                    ack_msg = can.Message(arbitration_id=0x33, data=[0x03, 0x74, 0x01, 0x02],
                                          is_extended_id=extended_flag, is_fd=fd_flag)
                    print("ack_msg")
                    print(ack_msg)
                    flg = True
                    time-=1
                elif msg.data[1] == 0x36 and msg.data[2] == 0x01:
                    message.append( msg.data[3])
                    message.append( msg.data[4])
                    ack_msg = can.Message(arbitration_id=0x33, data=[0x02, 0x76, 0x01],
                                          is_extended_id=extended_flag, is_fd=fd_flag)
                    time -= 1
                    flg = True

                elif msg.data[1] == 0x36 and msg.data[2] == 0x02:
                    message.append( msg.data[3])
                    message.append( msg.data[4])
                    logger.info(f"Complete msg received: {message}")
                    ack_msg = can.Message(arbitration_id=0x33, data=[0x02, 0x76, 0x02],
                                          is_extended_id=extended_flag, is_fd=fd_flag)
                    time -= 1
                    flg = True

                elif msg.data[1] == 0x37:
                    ack_msg = can.Message(arbitration_id=0x33, data=[0x01, 0x77],
                                          is_extended_id=extended_flag, is_fd=fd_flag)
                    time -= 1
                    flg = True

                elif msg.data[1] == 0x31:
                    memory = msg.data[5]
                    memoryAddress = msg.data[6]
                    memorySize = msg.data[7]
                    logger.info("Message address = 0x%X and memorySize= 0x%X",
                                memoryAddress, memorySize)

                    ack_msg = can.Message(arbitration_id=0x33, data=[0x03, 0x01, 0xff, 0x00],
                                          is_extended_id=extended_flag, is_fd=fd_flag)
                    time -= 1
                    flg = True

                # Send acknowledgment
                try:
                    if (msg.data[0]==0x03 or msg.data[0]==0x02 or msg.data[1] == 0x11 or flg) and time >0:
                        bus.send(ack_msg)
                        print("ack message",ack_msg)

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