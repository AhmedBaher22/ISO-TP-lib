from typing import Callable, List, Optional
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)

from uds_layer.uds_enums import CommunicationControlSubFunction, CommunicationControlType, SessionType, OperationType, OperationStatus
from uds_layer.operation import Operation
from uds_layer.transfer_request import TransferRequest
from uds_layer.transfer_enums import CheckSumMethod, TransferStatus, EncryptionMethod, CompressionMethod
from logger import Logger, LogType, ProtocolType
import zlib  # For CRC32 calculation
from crccheck.crc import Crc16

class Server:
    def __init__(self, can_id: [int],client_send:Callable):
        self._can_id = can_id
        self._session = SessionType.NONE
        self._pending_operations: List[Operation] = []
        self._completed_operations: List[Operation] = []
        self._logs: List[str] = []
        self._p2_timing = 0
        self._p2_star_timing = 0
        self.transfer_requests: List[TransferRequest] = []
        self._logger = Logger(ProtocolType.UDS)
        self.clientSend:Callable=client_send
    # Getters and setters
    @property
    def can_id(self) -> [int]:
        return self._can_id

    @property
    def session(self) -> SessionType:
        return self._session

    @session.setter
    def session(self, value: SessionType):
        self._session = value

    @property
    def p2_timing(self) -> int:
        return self._p2_timing

    @p2_timing.setter
    def p2_timing(self, value: int):
        self._p2_timing = value

    @property
    def p2_star_timing(self) -> int:
        return self._p2_star_timing

    @p2_star_timing.setter
    def p2_star_timing(self, value: int):
        self._p2_star_timing = value

    # List operations
    def add_pending_operation(self, operation: Operation):
        self._pending_operations.append(operation)

    def remove_pending_operation(self, operation: Operation):
        self._pending_operations.remove(operation)

    def add_completed_operation(self, operation: Operation):
        self._completed_operations.append(operation)

    def add_log(self, log: str):
        self._logs.append(log)

    def get_pending_operation_by_type(self, operation_type: OperationType) -> Operation:

        for operation in self._pending_operations:

            if operation.operation_type == operation_type:

                return operation
        return None

    def check_access_required(self, operation_type: OperationType) -> bool:
        # Define minimum session requirements for each operation
        session_requirements = {
            OperationType.READ_DATA_BY_IDENTIFIER: [SessionType.DEFAULT, SessionType.EXTENDED, SessionType.PROGRAMMING],
            OperationType.WRITE_DATA_BY_IDENTIFIER: [SessionType.EXTENDED, SessionType.PROGRAMMING],
            OperationType.ECU_RESET: [SessionType.EXTENDED, SessionType.PROGRAMMING],
            OperationType.TRANSFER_DATA: [SessionType.PROGRAMMING],
            OperationType.REQUEST_DOWNLOAD: [SessionType.PROGRAMMING],
            OperationType.REQUEST_TRANSFER_EXIT: [SessionType.PROGRAMMING]
        }

        required_sessions = session_requirements.get(operation_type, [])
        return self._session in required_sessions

    def read_data_by_identifier(self, vin: List[int]) -> List[int]:
        if not self.check_access_required(OperationType.READ_DATA_BY_IDENTIFIER):
            error_msg = f"Error: Insufficient session level for READ_DATA_BY_IDENTIFIER. Current session: {self._session}"
            print(error_msg)
            self.add_log(error_msg)
            return [0x00]

        message = [0x22] # Request for VIN (F190)
        for e in vin:
            message.append(e)
        operation = Operation(OperationType.READ_DATA_BY_IDENTIFIER, message)
        self.add_pending_operation(operation)
        
        log_msg = f"Created READ_DATA_BY_IDENTIFIER operation for VIN. Message: {[message]}"
        self.add_log(log_msg)
        
        return message

    def on_read_data_by_identifier_respond(self, operation_status: int, message: List[int], vin: Optional[str] = None):
        if operation_status == 0x62:  # Positive response
            data_str = ' '.join([hex(x) for x in message])
            response_msg = f"Read Data Success - Data: {data_str}, VIN: {vin}"
            print(response_msg)
            self.add_log(response_msg)
        elif operation_status == 0x7F:  # Negative response
            nrc = message[0]
            nrc_descriptions = {
                0x10: "General Reject",
                0x11: "Service Not Supported",
                0x12: "Sub-Function Not Supported",
                0x13: "Invalid Format",
                0x22: "Conditions Not Correct",
                0x31: "Request Out Of Range",
                0x33: "Security Access Denied",
                0x35: "Invalid Key",
                0x36: "Exceed Number Of Attempts",
                0x37: "Required Time Delay Not Expired",
                
            }
            error_msg = f"Read Data Failed - NRC: {hex(nrc)} - {nrc_descriptions.get(nrc, 'Unknown Error')}"
            print(error_msg)
            self.add_log(error_msg)

    def write_data_by_identifier(self, vin: List[int], data: List[int]) -> List[int]:
        if not self.check_access_required(OperationType.WRITE_DATA_BY_IDENTIFIER):
            error_msg = f"Error: Insufficient session level for WRITE_DATA_BY_IDENTIFIER. Current session: {self._session}"
            print(error_msg)
            self.add_log(error_msg)
            return [0x00]

        # Prepare message: service ID (2E) + VIN identifier (F190) + data
        message = [0x2E]
        for e in vin:
            message.append(e)
        
        # Create and add operation
        operation = Operation(OperationType.WRITE_DATA_BY_IDENTIFIER, message)
        self.add_pending_operation(operation)
        
        log_msg = f"Created WRITE_DATA_BY_IDENTIFIER operation for VIN. Message: {[hex(x) for x in message]}"
        self.add_log(log_msg)
        
        return message

    def on_write_data_by_identifier_respond(self, operation_status: int, message: List[int], vin: Optional[str] = None):

        operation = self.get_pending_operation_by_type(OperationType.WRITE_DATA_BY_IDENTIFIER)
             
        if operation:
  
            if operation_status == 0x6E:  # Positive response

                operation.status = OperationStatus.COMPLETED

                success_msg = f"Write Data Success - VIN: {vin} has been successfully updated"
                print(success_msg)
                self.add_log(success_msg)
                operation.status = OperationStatus.COMPLETED
            
            elif operation_status == 0x7F:  # Negative response
                nrc = message[0]
                nrc_descriptions = {
                    0x10: "General Reject",
                    0x11: "Service Not Supported",
                    0x12: "Sub-Function Not Supported",
                    0x13: "Invalid Format",
                    0x22: "Conditions Not Correct",
                    0x31: "Request Out Of Range",
                    0x33: "Security Access Denied",
                    0x35: "Invalid Key",
                    0x36: "Exceed Number Of Attempts",
                    0x37: "Required Time Delay Not Expired",
                    # Add more NRC codes as needed
                }
                operation.status = OperationStatus.REJECTED

                error_msg = f"Write Data Failed - NRC: {hex(nrc)} - {nrc_descriptions.get(nrc, 'Unknown Error')}"
                print(error_msg)
                self.add_log(error_msg)
                operation.status = OperationStatus.REJECTED

            # Move operation to completed operations
            self.remove_pending_operation(operation)
            self.add_completed_operation(operation)


    def ecu_reset(self, reset_type: int) -> List[int]:
        if not self.check_access_required(OperationType.ECU_RESET):
            error_msg = f"Error: Insufficient session level for ECU_RESET. Current session: {self._session}"
            print(error_msg)
            self.add_log(error_msg)
            return [0x00]

        # Prepare message: service ID (11) + reset type
        message = [0x11, reset_type]
        
        # Create and add operation
        operation = Operation(OperationType.ECU_RESET, message)
        self.add_pending_operation(operation)
        
        # Create log message with reset type description
        reset_types = {
            0x01: "Hard Reset",
            0x02: "Key Off/On Reset",
            0x03: "Soft Reset",
            0x04: "Enable Rapid Power Shutdown",
            0x05: "Disable Rapid Power Shutdown"
        }
        reset_description = reset_types.get(reset_type, "Unknown Reset Type")
        
        log_msg = f"Created ECU_RESET operation. Reset Type: {reset_description} ({hex(reset_type)}). Message: {[hex(x) for x in message]}"
        self.add_log(log_msg)
        
        return message

    def on_ecu_reset_respond(self, operation_status: int, message: List[int], reset_type: Optional[int] = None):
        operation = self.get_pending_operation_by_type(OperationType.ECU_RESET)
        
        if operation:
            if operation_status == 0x51:  # Positive response
                reset_types = {
                    0x01: "Hard Reset",
                    0x02: "Key Off/On Reset",
                    0x03: "Soft Reset",
                    0x04: "Enable Rapid Power Shutdown",
                    0x05: "Disable Rapid Power Shutdown"
                }
                reset_description = reset_types.get(reset_type, "Unknown Reset Type")
                
                success_msg = f"ECU Reset Success - Type: {reset_description} ({hex(reset_type) if reset_type else 'Unknown'})"
                if len(message) > 0:  # If there's additional power down time information
                    success_msg += f", Power Down Time: {message[0]} seconds"
                
                print(success_msg)
                self.add_log(success_msg)
                operation.status = OperationStatus.COMPLETED
            
            elif operation_status == 0x7F:  # Negative response
                nrc = message[0]
                nrc_descriptions = {
                    0x10: "General Reject",
                    0x11: "Service Not Supported",
                    0x12: "Sub-Function Not Supported",
                    0x13: "Invalid Format",
                    0x22: "Conditions Not Correct",
                    0x31: "Request Out Of Range",
                    0x33: "Security Access Denied",
                    0x35: "Invalid Key",
                    0x36: "Exceed Number Of Attempts",
                    0x37: "Required Time Delay Not Expired",
                    0x72: "General Programming Failure",
                    # Add more NRC codes as needed
                }
                error_msg = f"ECU Reset Failed - NRC: {hex(nrc)} - {nrc_descriptions.get(nrc, 'Unknown Error')}"
                print(error_msg)
                self.add_log(error_msg)
                operation.status = OperationStatus.REJECTED

            # Move operation to completed operations
            self.remove_pending_operation(operation)
            self.add_completed_operation(operation)

    def transfer_data(self):
        pass

    def request_download(self, transfer_request: TransferRequest) -> List[int]:
        self._logger.log_message(
            log_type=LogType.INFO,
            message=f"Request download function for {transfer_request.recv_DA} is being processing and preparing message"
            )
                
        if not self.check_access_required(OperationType.REQUEST_DOWNLOAD):
            error_msg = f"Error: Insufficient session level for REQUEST_DOWNLOAD. Current session: {self._session}"
            # print(error_msg)
            self._logger.log_message(
            log_type=LogType.ERROR,
            message=error_msg)
            self.add_log(error_msg)
            return [0x00]


        # Calculate DataFormatIdentifier
        data_format_identifier = (transfer_request.compression_method.value << 4) | transfer_request.encryption_method.value

        # Calculate AddressAndLengthFormatIdentifier
        address_length = len(transfer_request.memory_address)
        size_length = len(str(transfer_request.data_size))
        address_length_format_identifier = (address_length << 4) | size_length

        # Prepare message
        message = [0x34, data_format_identifier, address_length_format_identifier]
        
        # Add memory address
        message.extend(transfer_request.memory_address)
        
        # Add memory size
        size_bytes = transfer_request.data_size.to_bytes(size_length, byteorder='big')
        message.extend(size_bytes)

        # Update transfer request and add to list
        transfer_request.status = TransferStatus.CREATED
        self.transfer_requests.append(transfer_request)

        log_msg = f"Created REQUEST_DOWNLOAD operation for Diagnostic address {transfer_request.recv_DA}. Message: {[hex(x) for x in message]}"
        self._logger.log_message(
            log_type=LogType.INFO,
            message=log_msg)        
        self.add_log(log_msg)
        
        return message

    def on_request_download_respond(self, message: List[int]):

        # Find transfer request with CREATED status
        transfer_request = next((req for req in self.transfer_requests 
                               if req.status == TransferStatus.CREATED), None)
        
        if not transfer_request:
            error_msg = "No pending transfer request found"
            self._logger.log_message(
                log_type=LogType.ERROR,
                message=error_msg
            )
            self.add_log(error_msg)
            return
        
        self._logger.log_message(
            log_type=LogType.INFO,
            message=f"Request download respond for {transfer_request.recv_DA} received with message : {[hex(x) for x in message]}")
        
        if message[0] == 0x74:  # Positive response
            self._logger.log_message(
            log_type=LogType.INFO,
            message=f"Request download respond for {transfer_request.recv_DA} is positive")

            length_format_identifier = message[1]
            block_length_bytes = message[2:2+length_format_identifier]
            
            # Calculate MaxNumberOfBlockLength
            transfer_request.max_number_of_block_length = int.from_bytes(block_length_bytes, 'big')
            
            # Calculate steps number
            transfer_request.calculate_steps_number()
            
            # Update status and counter
            transfer_request.status = TransferStatus.SENDING_BLOCKS_IN_PROGRESS
            transfer_request.current_number_of_steps = 0
            
            # Start transfer data
            message=self.transfer_data(transfer_request)



            self.clientSend(message=message,server_can_id=self.can_id)
            self._logger.log_message(
            log_type=LogType.ACKNOWLEDGMENT,
            message=f"Transfer data request for {transfer_request.recv_DA} sended with message : {[hex(x) for x in message]}")

        elif message[0] == 0x7F and message[1] == 0x34:  # Negative response
            self._logger.log_message(
            log_type=LogType.INFO,
            message=f"Request download respond for {transfer_request.recv_DA} is negative")

            transfer_request.NRC = message[2]
            transfer_request.status = TransferStatus.REJECTED
            
            nrc_descriptions = {
                0x10: "General Reject",
                0x11: "Service Not Supported",
                0x12: "Sub-Function Not Supported",
                0x13: "Invalid Format",
                0x22: "Conditions Not Correct",
                0x31: "Request Out Of Range",
                0x33: "Security Access Denied",
                0x70: "Upload/Download Not Accepted",
                # Add more NRC codes as needed
            }
            
            error_msg = f"Download Request Failed - NRC: {hex(transfer_request.NRC)} - {nrc_descriptions.get(transfer_request.NRC, 'Unknown Error')}"
            self._logger.log_message(
            log_type=LogType.error,
            message=error_msg)
            self.add_log(error_msg)


    def transfer_data(self, transfer_request: TransferRequest) -> List[int]:
        self._logger.log_message(
            log_type=LogType.INFO,
            message=f"Transfer data function for {transfer_request.recv_DA} is being processing and preparing message")
                        
        if transfer_request.status != TransferStatus.SENDING_BLOCKS_IN_PROGRESS:
            error_msg = f"Invalid transfer status for TRANSFER_DATA: {transfer_request.status}"
            self._logger.log_message(
            log_type=LogType.ERROR,
            message=error_msg)
                
            self.add_log(error_msg)
            return [0x00]

        # Prepare BlockSequenceCounter
        block_sequence_counter = (transfer_request.current_number_of_steps + 1) % 0xFF

        # If block_sequence_counter wrapped around to 0, increment iteration
        if block_sequence_counter == 0:
            transfer_request.iteration += 1

        # Calculate actual data position using iteration and block_sequence_counter
        actual_position = ((transfer_request.iteration - 1) * 0xFF + block_sequence_counter - 1) * transfer_request.max_number_of_block_length

        # Calculate data slice indices
        if transfer_request.max_number_of_block_length == 0:
            # Use all data if MaxNumberOfBlockLength is 0
            data_record = list(transfer_request.data)
        else:
            end_idx = min(actual_position + transfer_request.max_number_of_block_length, 
                        transfer_request.data_size)
            data_record = list(transfer_request.data[actual_position:end_idx])

        # Prepare message
        message = [0x36, block_sequence_counter] + data_record

        # Increment counter with modulus to stay within byte range
        transfer_request.current_number_of_steps = (transfer_request.current_number_of_steps + 1) % 0xFF

        log_msg = (f"Created TRANSFER_DATA message. Block: {block_sequence_counter}, "
                f"Iteration: {transfer_request.iteration}, "
                f"Actual Position: {actual_position}, "
                f"Data size: {len(data_record)}")
        self.add_log(log_msg)
        self._logger.log_message(
            log_type=LogType.INFO,
            message=log_msg
        )
        
        return message

    def on_transfer_data_respond(self, message: List[int]):

        transfer_request = next((req for req in self.transfer_requests 
                               if req.status == TransferStatus.SENDING_BLOCKS_IN_PROGRESS), None)
        
        if not transfer_request:
            error_msg = "No transfer request in progress"
            self._logger.log_message(
                log_type=LogType.ERROR,
                message=error_msg
            )
            self.add_log(error_msg)
            return
        
        self._logger.log_message(
            log_type=LogType.INFO,
            message=f"Transfer data respond for {transfer_request.recv_DA} received with message : {[hex(x) for x in message]}")
        
        if message[0] == 0x76:  # Positive response
            self._logger.log_message(
            log_type=LogType.INFO,
            message=f"Request download respond for {transfer_request.recv_DA} is postitive")
                    
            block_sequence_counter = message[1]
            
            if block_sequence_counter != transfer_request.current_number_of_steps:
                transfer_request.status = TransferStatus.REJECTED
                transfer_request.NRC = 0x73  # Wrong Block Sequence Counter
                error_msg = "Wrong Block Sequence Counter"
                self._logger.log_message(
                log_type=LogType.INFO,
                 message=error_msg)
        
                self.add_log(error_msg)
                return

            if (transfer_request.current_number_of_steps * transfer_request.max_number_of_block_length 
                    > transfer_request.data_size) or transfer_request.max_number_of_block_length == 0:
                transfer_request.status = TransferStatus.COMPLETED
                message= self.request_transfer_exit(transfer_request)
                self.clientSend(message=message,server_can_id=self.can_id)
                self._logger.log_message(
                log_type=LogType.ACKNOWLEDGMENT,
                message=f"Transfer data request for {transfer_request.recv_DA} sended with message : {[hex(x) for x in message]}")                
            else:
                message= self.transfer_data(transfer_request)
                self._logger.log_message(
                log_type=LogType.ACKNOWLEDGMENT,
                message=f"Transfer Exit request for {transfer_request.recv_DA} sended with message : {[hex(x) for x in message]}")                
                self.clientSend(message=message,server_can_id=self.can_id)

        elif message[0] == 0x7F:  # Negative response
            transfer_request.status = TransferStatus.REJECTED
            transfer_request.NRC = message[2]
            error_msg = f"Transfer Data Failed - NRC: {hex(transfer_request.NRC)}"
            self._logger.log_message(
            log_type=LogType.ERROR,
            message=error_msg)
            self.add_log(error_msg)

    def request_transfer_exit(self, transfer_request: TransferRequest) -> List[int]:
        self._logger.log_message(
            log_type=LogType.INFO,
            message=f"Transfer Exit request function for {transfer_request.recv_DA} is being processing and preparing message")
                               
        if transfer_request.status != TransferStatus.COMPLETED:
            error_msg = f"Invalid transfer status for REQUEST_TRANSFER_EXIT: {transfer_request.status}"
            self._logger.log_message(
                log_type=LogType.ERROR,
                message=error_msg)
                        
            self.add_log(error_msg)
            return [0x00]

        # if transfer_request.checksum_required:
        #     crc = self.calculate_crc32(transfer_request.data)
        #     message = [0x37]
        #     print(f"crc: {crc}")
        #     message.append(crc)
        #     # message.append(crc)
        # else:
        message = [0x37]

        log_msg = f"Created REQUEST_TRANSFER_EXIT message. Checksum: {transfer_request.checksum_required}"
        self.add_log(log_msg)
        self._logger.log_message(
            log_type=LogType.INFO,
            message=log_msg
        )        
        return message

    def on_request_transfer_exit_respond(self, message: List[int]):

        transfer_request = next((req for req in self.transfer_requests 
                               if req.status == TransferStatus.COMPLETED), None)
        
        if not transfer_request:
            error_msg = "No completed transfer request found"
            print(error_msg)
            self.add_log(error_msg)
            return
        self._logger.log_message(
            log_type=LogType.INFO,
            message=f"Transfer Exit respond for {transfer_request.recv_DA} received with message : {[hex(x) for x in message]}")
        
        if message[0] == 0x77:  # Positive response
            transfer_request.status = TransferStatus.CHECKING_CRC
            if  transfer_request.checksum_required == CheckSumMethod.NO_CHECKSUM:
                transfer_request.status = TransferStatus.CLOSED_SUCCESSFULLY
                success_msg = f"Transfer completed successfully for ECU with diagnostic address : {self.can_id}"
                self._logger.log_message(
                log_type=LogType.ACKNOWLEDGMENT,
                message=success_msg)
                self.add_log(success_msg)
                return
            else:
                print("da5l hett check memory")
                message=self.check_memory(transfer_request)
                print("reg3 mn check memory")
                self.clientSend(message=message,server_can_id=self.can_id)
                self._logger.log_message(
                log_type=LogType.ACKNOWLEDGMENT,
                message=f"Check Memory subroutine service for {transfer_request.recv_DA} sended with message : {[hex(x) for x in message]}") 

            self.add_log(success_msg)
        
        elif message[0] == 0x7F:  # Negative response
            transfer_request.status = TransferStatus.REJECTED
            transfer_request.NRC = message[2]
            error_msg = f"Transfer Exit Failed - NRC: {hex(transfer_request.NRC)}"
            self._logger.log_message(
            log_type=LogType.ERROR,
            message=error_msg)
            self.add_log(error_msg)

    def communication_control(self, sub_function: CommunicationControlSubFunction, 
                            control_type: CommunicationControlType) -> List[int]:
        if not self.check_access_required(OperationType.COMMUNICATION_CONTROL):
            error_msg = f"Error: Insufficient session level for COMMUNICATION_CONTROL. Current session: {self._session}"
            print(error_msg)
            self.add_log(error_msg)
            return [0x00]

        # Prepare message
        message = [0x28, sub_function.value, control_type.value, 0x00]  # Reserved byte is 0x00

        # Create and add operation
        operation = Operation(OperationType.COMMUNICATION_CONTROL, message)
        self.add_pending_operation(operation)

        log_msg = (f"Created COMMUNICATION_CONTROL operation. "
                  f"SubFunction: {sub_function.name}, ControlType: {control_type.name}")
        self.add_log(log_msg)

        return message

    def on_communication_control_respond(self, message: List[int]):
        if message[0] == 0x68:  # Positive response
            # Find matching operation based on SubFunction and ControlType
            operation = next((op for op in self._pending_operations 
                            if op.operation_type == OperationType.COMMUNICATION_CONTROL 
                            and op.message[1] == message[1]  # SubFunction matches
                            and op.message[2] == message[2]  # ControlType matches
                            ), None)

            if operation:
                operation.status = OperationStatus.COMPLETED
                self.remove_pending_operation(operation)
                self.add_completed_operation(operation)

                sub_function = CommunicationControlSubFunction(message[1])
                control_type = CommunicationControlType(message[2])
                
                success_msg = (f"Communication Control Success - "
                             f"SubFunction: {sub_function.name}, "
                             f"ControlType: {control_type.name}")
                print(success_msg)
                self.add_log(success_msg)

        elif message[0] == 0x7F and message[1] == 0x28:  # Negative response
            operation = next((op for op in self._pending_operations 
                            if op.operation_type == OperationType.COMMUNICATION_CONTROL), None)
            
            if operation:
                operation.status = OperationStatus.REJECTED
                self.remove_pending_operation(operation)
                self.add_completed_operation(operation)

                nrc = message[2]
                nrc_descriptions = {
                    0x10: "General Reject",
                    0x11: "Service Not Supported",
                    0x12: "Sub-Function Not Supported",
                    0x13: "Invalid Format",
                    0x22: "Conditions Not Correct",
                    0x31: "Request Out Of Range",
                    0x33: "Security Access Denied",
                    0x70: "Upload/Download Not Accepted",
                    # Add more NRC codes as needed
                }
                
                error_msg = f"Communication Control Failed - NRC: {hex(nrc)} - {nrc_descriptions.get(nrc, 'Unknown Error')}"
                print(error_msg)
                self.add_log(error_msg)

    def erase_memory(self, memory_address: bytearray, memory_size: bytearray) -> List[int]:
        if not self.check_access_required(OperationType.ERASE_MEMORY):
            error_msg = f"Error: Insufficient session level for ERASE_MEMORY. Current session: {self._session}"
            print(error_msg)
            self.add_log(error_msg)
            return [0x00]

        # Calculate AddressAndSizeFormat
        address_length = len(memory_address)
        size_length = len(memory_size)
        address_and_size_format = (address_length << 4) | size_length

        # Prepare message
        message = [0x31, 0x01, 0xFF, 0x00, address_and_size_format]
        message.extend(memory_address)
        message.extend(memory_size)
        message.append(0x00)  # Reserved byte

        # Create and add operation
        operation = Operation(OperationType.ERASE_MEMORY, message)
        self.add_pending_operation(operation)

        log_msg = (f"Created ERASE_MEMORY operation. "
                  f"Address Length: {address_length}, "
                  f"Size Length: {size_length}, "
                  f"Address: {[hex(x) for x in memory_address]}, "
                  f"Size: {[hex(x) for x in memory_size]}")
        self.add_log(log_msg)

        return message

    def on_erase_memory_respond(self, message: List[int]):
        if message[0] == 0x71:  # Positive response
            # Find matching operation based on routine identifier bytes
            operation = next((op for op in self._pending_operations 
                            if op.operation_type == OperationType.ERASE_MEMORY 
                            and op.message[1] == message[1]  # 0x01
                            and op.message[2] == message[2]  # 0xFF
                            and op.message[3] == message[3]  # 0x00
                            ), None)

            if operation:
                operation.status = OperationStatus.COMPLETED
                self.remove_pending_operation(operation)
                self.add_completed_operation(operation)

                success_msg = "Memory Erase Operation Completed Successfully"
                print(success_msg)
                self.add_log(success_msg)

        elif message[0] == 0x7F and message[1] == 0x31:  # Negative response
            operation = next((op for op in self._pending_operations 
                            if op.operation_type == OperationType.ERASE_MEMORY), None)
            
            if operation:
                operation.status = OperationStatus.REJECTED
                self.remove_pending_operation(operation)
                self.add_completed_operation(operation)

                nrc = message[2]
                nrc_descriptions = {
                    0x10: "General Reject",
                    0x11: "Service Not Supported",
                    0x12: "Sub-Function Not Supported",
                    0x13: "Invalid Format",
                    0x22: "Conditions Not Correct",
                    0x31: "Request Out Of Range",
                    0x33: "Security Access Denied",
                    0x72: "General Programming Failure",
                    # Add more NRC codes as needed
                }
                
                error_msg = f"Memory Erase Failed - NRC: {hex(nrc)} - {nrc_descriptions.get(nrc, 'Unknown Error')}"
                print(error_msg)
                self.add_log(error_msg)


    def check_memory(self, transfer_request: TransferRequest) -> List[int]:
        if transfer_request.status != TransferStatus.CHECKING_CRC:
            error_msg = f"Invalid transfer status for CHECK_MEMORY: {transfer_request.status}"
            print(error_msg)
            self.add_log(error_msg)
            return [0x00]

        # Prepare base message
        message = [0x31, 0x01, 0xFF, 0x01, transfer_request.checksum_required.value]

        # Calculate and add checksum based on method
        if transfer_request.checksum_required == CheckSumMethod.CRC_16:
            print("da5l condition l crc16")
            checksum = self.calculate_crc16(transfer_request.data)
            print("rg3 mn crc 16")
            message.extend(checksum)
            print("m3rf4 y3ml extend")
            log_msg = f"Using CRC-16 checksum: {[hex(x) for x in checksum]}"
        elif transfer_request.checksum_required == CheckSumMethod.CRC_32:
            try:
                print("da5l condition l crc32")
                checksum = self.calculate_crc32(transfer_request.data)
                print(f"reg3 w hasb l crc32={checksum}")
                message.extend(checksum)
                print("lmessage al gdeda",message)
                log_msg = f"Using CRC-32 checksum: {[hex(x) for x in checksum]}"
            except Exception as e:
                print(e)                
        else:
            log_msg = "No checksum required"

        self.add_log(log_msg)
        log_msg = f"Created CHECK_MEMORY operation. Message: {[hex(x) for x in message]}"
        self.add_log(log_msg)
        
        return message

    def on_check_memory_respond(self, message: List[int]):
        # Find transfer request with CHECKING_CRC status
        transfer_request = next((req for req in self.transfer_requests 
                               if req.status == TransferStatus.CHECKING_CRC), None)
        
        if not transfer_request:
            error_msg = "No transfer request in CRC checking state"
            print(error_msg)
            self.add_log(error_msg)
            return

        if message[0] == 0x71:  # Positive response
            if (message[1] == 0x01 and 
                message[2] == 0xFF and 
                message[3] == 0x01):  # Validate routine identifier
                
                transfer_request.status = TransferStatus.CLOSED_SUCCESSFULLY
                success_msg = (f"Memory Check Success - Checksum verified using "
                             f"{transfer_request.checksum_required.name}")
                
                print(success_msg)
                self.add_log(success_msg)
                success_msg = f"Transfer completed successfully for ECU with diagnostic address : {self.can_id}"
                self._logger.log_message(
                log_type=LogType.ACKNOWLEDGMENT,
                message=success_msg)
                self.add_log(success_msg)                
                
            
        elif message[0] == 0x7F:  # Negative response
            transfer_request.status = TransferStatus.REJECTED
            transfer_request.NRC = message[2]
            
            nrc_descriptions = {
                0x10: "General Reject",
                0x11: "Service Not Supported",
                0x12: "Sub-Function Not Supported",
                0x13: "Invalid Format",
                0x22: "Conditions Not Correct",
                0x24: "Request Sequence Error",
                0x31: "Request Out Of Range",
                0x72: "General Programming Failure",
                0x73: "Wrong Block Sequence Counter",
                0x77: "Checksum Verification Failed",
                # Add more NRC codes as needed
            }
            
            error_msg = (f"Memory Check Failed - NRC: {hex(transfer_request.NRC)} - "
                        f"{nrc_descriptions.get(transfer_request.NRC, 'Unknown Error')}")
            print(error_msg)
            self.add_log(error_msg)
            
    def get_pending_operations(self):
        return self._pending_operations
    
    def calculate_crc16(self, data: bytearray) -> bytearray:
        crc = Crc16.calc(data)
        return crc.to_bytes(2, byteorder='big')

    def calculate_crc32(self, data: bytearray) -> bytearray:
        # Convert data to bytes if it's not already
        if isinstance(data, list):
            data = bytes(data)
        elif isinstance(data, bytearray):
            data = bytes(data)
            
        crc = zlib.crc32(data) & 0xFFFFFFFF
        return crc.to_bytes(4, byteorder='big')
    
# def calculate_crc32(data: bytearray) -> bytearray:
#     crc = zlib.crc32(data) & 0xFFFFFFFF
#     return crc.to_bytes(4, byteorder='big')
# data=[0x52, 0x55, 0x32]
# data=bytearray(data)
# print(data)
# checksu=calculate_crc32(data=data)  
# print(checksu)
# data.extend(checksu)
# print(data)