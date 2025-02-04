from typing import List, Optional
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from uds_layer.uds_enums import SessionType, OperationType, OperationStatus
from uds_layer.operation import Operation
from uds_layer.transfer_request import TransferRequest
from uds_layer.transfer_enums import TransferStatus, EncryptionMethod, CompressionMethod
import zlib  # For CRC32 calculation

class Server:
    def __init__(self, can_id: [int]):
        self._can_id = can_id
        self._session = SessionType.NONE
        self._pending_operations: List[Operation] = []
        self._completed_operations: List[Operation] = []
        self._logs: List[str] = []
        self._p2_timing = 0
        self._p2_star_timing = 0
        self.transfer_requests: List[TransferRequest] = []

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
        if not self.check_access_required(OperationType.REQUEST_DOWNLOAD):
            error_msg = f"Error: Insufficient session level for REQUEST_DOWNLOAD. Current session: {self._session}"
            print(error_msg)
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

        log_msg = f"Created REQUEST_DOWNLOAD operation. Message: {[hex(x) for x in message]}"
        self.add_log(log_msg)
        
        return message

    def on_request_download_respond(self, message: List[int]):
        # Find transfer request with CREATED status
        transfer_request = next((req for req in self.transfer_requests 
                               if req.status == TransferStatus.CREATED), None)
        
        if not transfer_request:
            error_msg = "No pending transfer request found"
            print(error_msg)
            self.add_log(error_msg)
            return

        if message[0] == 0x74:  # Positive response
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
            self.transfer_data(transfer_request)
            
        elif message[0] == 0x7F and message[1] == 0x34:  # Negative response
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
            print(error_msg)
            self.add_log(error_msg)


    def transfer_data(self, transfer_request: TransferRequest) -> List[int]:
        if transfer_request.status != TransferStatus.SENDING_BLOCKS_IN_PROGRESS:
            error_msg = f"Invalid transfer status for TRANSFER_DATA: {transfer_request.status}"
            print(error_msg)
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
        
        return message

    def on_transfer_data_respond(self, message: List[int]):
        transfer_request = next((req for req in self.transfer_requests 
                               if req.status == TransferStatus.SENDING_BLOCKS_IN_PROGRESS), None)
        
        if not transfer_request:
            error_msg = "No transfer request in progress"
            print(error_msg)
            self.add_log(error_msg)
            return

        if message[0] == 0x76:  # Positive response
            block_sequence_counter = message[1]
            
            if block_sequence_counter != transfer_request.current_number_of_steps:
                transfer_request.status = TransferStatus.REJECTED
                transfer_request.NRC = 0x73  # Wrong Block Sequence Counter
                error_msg = "Wrong Block Sequence Counter"
                print(error_msg)
                self.add_log(error_msg)
                return

            if (transfer_request.current_number_of_steps * transfer_request.max_number_of_block_length 
                    > transfer_request.data_size) or transfer_request.max_number_of_block_length == 0:
                transfer_request.status = TransferStatus.COMPLETED
                return self.request_transfer_exit(transfer_request)
            else:
                return self.transfer_data(transfer_request)

        elif message[0] == 0x7F:  # Negative response
            transfer_request.status = TransferStatus.REJECTED
            transfer_request.NRC = message[2]
            error_msg = f"Transfer Data Failed - NRC: {hex(transfer_request.NRC)}"
            print(error_msg)
            self.add_log(error_msg)

    def request_transfer_exit(self, transfer_request: TransferRequest) -> List[int]:
        if transfer_request.status != TransferStatus.COMPLETED:
            error_msg = f"Invalid transfer status for REQUEST_TRANSFER_EXIT: {transfer_request.status}"
            print(error_msg)
            self.add_log(error_msg)
            return [0x00]

        if transfer_request.checksum_required:
            crc = self.calculate_crc32(transfer_request.data)
            message = [0x37] + list(crc)
        else:
            message = [0x37]

        log_msg = f"Created REQUEST_TRANSFER_EXIT message. Checksum: {transfer_request.checksum_required}"
        self.add_log(log_msg)
        
        return message

    def on_request_transfer_exit_respond(self, message: List[int]):
        transfer_request = next((req for req in self.transfer_requests 
                               if req.status == TransferStatus.COMPLETED), None)
        
        if not transfer_request:
            error_msg = "No completed transfer request found"
            print(error_msg)
            self.add_log(error_msg)
            return

        if message[0] == 0x77:  # Positive response
            transfer_request.status = TransferStatus.CLOSED_SUCCESSFULLY
            success_msg = "Transfer completed successfully"
            print(success_msg)
            self.add_log(success_msg)
        
        elif message[0] == 0x7F:  # Negative response
            transfer_request.status = TransferStatus.REJECTED
            transfer_request.NRC = message[2]
            error_msg = f"Transfer Exit Failed - NRC: {hex(transfer_request.NRC)}"
            print(error_msg)
            self.add_log(error_msg)

    def get_pending_operations(self):
        return self._pending_operations
    
    def calculate_crc32(self, data: bytearray) -> bytearray:
        crc = zlib.crc32(data) & 0xFFFFFFFF
        return crc.to_bytes(4, byteorder='big')