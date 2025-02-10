import can
import logging
from can.interfaces.vector.exceptions import VectorInitializationError, VectorOperationError

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

import can
import logging
import time
from can.interfaces.vector.exceptions import VectorInitializationError, VectorOperationError

# Constants for CAN operation
MAX_QUEUE_SIZE = 64
QUEUE_TIMEOUT = 0.1
MAX_RETRIES = 3
RETRY_DELAY = 0.1

# [Your existing logger setup code remains the same...]

# Configuration parameters
fd_flag = False
extended_flag = False
channel_number = 0
bitrate = 500000
serial_number = 100
filterFlashCommand = [
    {"can_id": 0x33, "can_mask": 0x7FF, "extended": False}  # Exclude 0x0 messages
]

def check_channel_config(bus):
    try:
        logger.info(f"Connected to Vector device on channel {channel_number}")
        logger.info(f"Using transceiver: CANpiggy 1041Aopto")
        logger.info(f"Operating at bitrate: {bitrate} bit/s")
        return True
    except Exception as e:
        ErrorLogger.error(f"Channel configuration error: {e}")
        return False

def check_hardware_status(bus):
    for attempt in range(MAX_RETRIES):
        try:
            # Clear the transmit queue before testing
            if hasattr(bus, 'flush_tx_buffer'):
                bus.flush_tx_buffer()
            
            test_msg = can.Message(
                arbitration_id=0x7FF,
                data=[0, 0, 0, 0, 0, 0, 0, 0],
                is_extended_id=False
            )
            bus.send(test_msg, timeout=QUEUE_TIMEOUT)
            logger.info("Hardware status check passed")
            return True
        except VectorOperationError as e:
            if "XL_ERR_QUEUE_IS_FULL" in str(e):
                logger.warning(f"Transmit queue full, attempt {attempt + 1}/{MAX_RETRIES}")
                time.sleep(RETRY_DELAY)
                continue
            raise e
        except Exception as e:
            ErrorLogger.error(f"Hardware status check failed: {e}")
            raise e
    return False

def send_message_with_retry(bus, msg, max_retries=MAX_RETRIES):
    for attempt in range(max_retries):
        try:
            if hasattr(bus, 'flush_tx_buffer'):
                bus.flush_tx_buffer()
            
            bus.send(msg, timeout=QUEUE_TIMEOUT)
            logger.info(f"Message sent successfully: {msg}")
            return True
        except VectorOperationError as e:
            if "XL_ERR_QUEUE_IS_FULL" in str(e):
                logger.warning(f"Queue full, attempt {attempt + 1}/{max_retries}")
                time.sleep(RETRY_DELAY)
                continue
            raise e
    return False

try:
    # Initialize the CAN bus with the Vector interface
    with can.Bus(
        interface="vector",
        channel=channel_number,
        app_name="UDS",
        fd=fd_flag,
        bitrate=bitrate,
        serial=serial_number,
        receive_own_messages=False,
        single_handle=True,
        tx_queue_size=MAX_QUEUE_SIZE,
        rx_queue_size=MAX_QUEUE_SIZE
    ) as bus:
        
        if not check_channel_config(bus):
            raise Exception("Channel configuration verification failed")
        
        if not check_hardware_status(bus):
            raise Exception("Hardware status check failed")
        
        logger.info("CAN bus initialized successfully for receiving messages.")
        bus.set_filters(filterFlashCommand)
        # ack_msg = can.Message(
        #                 arbitration_id=0x33,
        #                 data=[0x06, 0x50, 0x03, 0x00, 0x55, 0x01, 0x55],
        #                 is_extended_id=extended_flag,
        #                 is_fd=fd_flag
        #             )                
        # send_message_with_retry(msg=ack_msg,bus=bus)        
        while True:
            try:

                msg = bus.recv(timeout=None)
                
                # Skip invalid messages
                if not msg or msg.arbitration_id == 0x0 or len(msg.data) == 0:
                    continue
                
                logger.info("Message received with arbitration_id=0x%X and data=%s , and hole message = %s", 
                          msg.arbitration_id, msg.data, msg)
                
                remaining_attempts = 5  # Instead of 'time' variable
                message = bytearray()
                ack_msg = None
                flg = False

                # Message handling logic
                if msg.data[0] == 0x02 and msg.data[1] == 0x10:
                    ack_msg = can.Message(
                        arbitration_id=0x33,
                        data=[0x06, 0x50, 0x03, 0x00, 0x55, 0x01, 0x55],
                        is_extended_id=extended_flag,
                        is_fd=fd_flag
                    )
                    remaining_attempts -= 1
                
                elif msg.data[0] == 0x03 and msg.data[1] == 0x22:
                    ack_msg = can.Message(
                        arbitration_id=0x33,
                        data=[0x04, 0x62, 0x01, 0x90, 0x55],
                        is_extended_id=extended_flag,
                        is_fd=fd_flag
                    )
                    remaining_attempts -= 1
                
                elif msg.data[1] == 0x11:
                    ack_msg = can.Message(
                        arbitration_id=0x33,
                        data=[0x03, 0x7F, 0x11, 0x12],
                        is_extended_id=extended_flag,
                        is_fd=fd_flag
                    )
                    remaining_attempts -= 1
                
                elif msg.data[1] == 0x2E:
                    ack_msg = can.Message(
                        arbitration_id=0x33,
                        data=[0x03, 0x6E, 0x01, 0x90],
                        is_extended_id=extended_flag,
                        is_fd=fd_flag
                    )
                    remaining_attempts -= 1

                elif msg.data[1] == 0x34:
                    logger.info("Request Download received")
                    ack_msg = can.Message(
                        arbitration_id=0x33,
                        data=[0x03, 0x74, 0x01, 0x02],
                        is_extended_id=extended_flag,
                        is_fd=fd_flag
                    )
                    logger.info(f"Download response: {ack_msg}")
                    flg = True
                    remaining_attempts -= 1
                
                elif msg.data[1] == 0x36 and msg.data[2] == 0x01:
                    message.append(msg.data[3])
                    message.append(msg.data[4])
                    ack_msg = can.Message(
                        arbitration_id=0x33,
                        data=[0x02, 0x76, 0x01],
                        is_extended_id=extended_flag,
                        is_fd=fd_flag
                    )
                    remaining_attempts -= 1
                    flg = True

                elif msg.data[1] == 0x36 and msg.data[2] == 0x02:
                    message.append(msg.data[3])
                    message.append(msg.data[4])
                    logger.info(f"Complete msg received: {message}")
                    ack_msg = can.Message(
                        arbitration_id=0x33,
                        data=[0x02, 0x76, 0x02],
                        is_extended_id=extended_flag,
                        is_fd=fd_flag
                    )
                    remaining_attempts -= 1
                    flg = True

                elif msg.data[1] == 0x37:
                    ack_msg = can.Message(
                        arbitration_id=0x33,
                        data=[0x01, 0x77],
                        is_extended_id=extended_flag,
                        is_fd=fd_flag
                    )
                    remaining_attempts -= 1
                    flg = True

                elif msg.data[1] == 0x31:
                    memory = msg.data[5]
                    memoryAddress = msg.data[6]
                    memorySize = msg.data[7]
                    logger.info("Message address = 0x%X and memorySize= 0x%X",
                              memoryAddress, memorySize)

                    ack_msg = can.Message(
                        arbitration_id=0x33,
                        data=[0x03, 0x01, 0xff, 0x00],
                        is_extended_id=extended_flag,
                        is_fd=fd_flag
                    )
                    remaining_attempts -= 1
                    flg = True

                # Send acknowledgment with retry mechanism
                if ack_msg and remaining_attempts > 0:
                    if not send_message_with_retry(bus, ack_msg):
                        logger.error("Failed to send acknowledgment after maximum retries")
                
            except VectorOperationError as e:
                logger.error(f"Vector operation error during message handling: {e}")
                time.sleep(RETRY_DELAY)
                continue
                
            except Exception as e:
                logger.error(f"Error during message handling: {e}")
                continue

except VectorInitializationError as e:
    ErrorLogger.error("Error: VectorInitializationError: %s", e)

except VectorOperationError as e:
    ErrorLogger.error(f"Vector hardware operation error: {e}")

except Exception as e:
    ErrorLogger.error(f"Unexpected error: {e}")

finally:
    logger.info("CAN receive operation complete.")
    if 'bus' in locals():
        try:
            bus.shutdown()
        except:
            pass