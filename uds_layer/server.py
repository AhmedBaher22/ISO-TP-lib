from typing import Callable, List, Optional
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)

from uds_layer.uds_enums import CommunicationControlSubFunction, CommunicationControlType, SessionType, OperationType, OperationStatus
from uds_layer.operation import Operation
from uds_layer.transfer_request import TransferRequest
from uds_layer.transfer_enums import CheckSumMethod, TransferStatus, EncryptionMethod, CompressionMethod, FlashingECUStatus
from logger import Logger, LogType, ProtocolType
import zlib  # For CRC32 calculation
from crccheck.crc import Crc16
from hex_parser.SRecordParser import DataRecord
from uds_layer.FlashingECU import FlashingECU
from ECDSA_handler.ECDSA import ECDSAConstants, ECDSAManager
class Server:
    server_request=1
    def __init__(self, can_id: [int],client_send:Callable,client_Segment_send:Callable):
        self._can_id = can_id
        self._session = SessionType.NONE
        self._pending_operations: List[Operation] = []
        self._completed_operations: List[Operation] = []
        self._logs: List[str] = []
        self._p2_timing = 0
        self._p2_star_timing = 0
        self.transfer_requests: List[TransferRequest] = []
        self.Flash_ECU_Segments_Request: List[FlashingECU] = []
        self._logger = Logger(ProtocolType.UDS)
        self.clientSend:Callable=client_send
        self.client_Segment_send:Callable=client_Segment_send
        self._ID=Server.server_request+1000
        Server.server_request+=1000
        self._current_req_offset=0
        self._current_req_id=self._current_req_offset+self._ID
    # Getters and setters
    @property
    def current_req_id(self) -> int:
        self._current_req_id=self._current_req_offset+self._ID
        self._current_req_offset+=1
        return self._current_req_id
    
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
            OperationType.REQUEST_TRANSFER_EXIT: [SessionType.PROGRAMMING],
            OperationType.ERASE_MEMORY:[SessionType.EXTENDED, SessionType.PROGRAMMING],
            OperationType.SECURITY_ACCESS:[SessionType.EXTENDED, SessionType.PROGRAMMING]
        }

        required_sessions = session_requirements.get(operation_type, [])
        return self._session in required_sessions

    def read_data_by_identifier(self, vin: List[int]) -> List[int]:
        if not self.check_access_required(OperationType.READ_DATA_BY_IDENTIFIER):
            error_msg = f"Error: Insufficient session level for READ_DATA_BY_IDENTIFIER. Current session: {self._session}"
            
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
            
            self.add_log(error_msg)

    def write_data_by_identifier(self, vin: List[int], data: List[int]) -> List[int]:
        if not self.check_access_required(OperationType.WRITE_DATA_BY_IDENTIFIER):
            error_msg = f"Error: Insufficient session level for WRITE_DATA_BY_IDENTIFIER. Current session: {self._session}"
            
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
                
                self.add_log(error_msg)
                operation.status = OperationStatus.REJECTED

            # Move operation to completed operations
            self.remove_pending_operation(operation)
            self.add_completed_operation(operation)


    def ecu_reset(self, reset_type: int) -> List[int]:
        if not self.check_access_required(OperationType.ECU_RESET):
            error_msg = f"Error: Insufficient session level for ECU_RESET. Current session: {self._session}"
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
                
                
                self.add_log(success_msg)
                operation.status = OperationStatus.COMPLETED

                transfer_request = next((req for req in self.Flash_ECU_Segments_Request 
                        if req.status == FlashingECUStatus.CLOSED_SUCCESSFULLY), None)
                
                if transfer_request != None:

                    transfer_request.status=FlashingECUStatus.RESET
                    success_msg = f"{transfer_request.get_req()}ECU with diagnostic address : {self.can_id} reset successfully after flashing. the ECU is running with the new updates successfully"
                    self._logger.log_message(
                    log_type=LogType.ACKNOWLEDGMENT,
                    message=success_msg)
                    transfer_request.successfull_flashing_response(transfer_request.Flashing_Request_ID)
            
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
                #print(error_msg)
                self.add_log(error_msg)
                operation.status = OperationStatus.REJECTED
                transfer_request = next((req for req in self.Flash_ECU_Segments_Request 
                        if req.status == FlashingECUStatus.CLOSED_SUCCESSFULLY), None)
                
                if transfer_request != None:

                    transfer_request.status=FlashingECUStatus.REJECTED
                    success_msg = f"{transfer_request.get_req()}ECU with diagnostic address : {self.can_id} reset successfully after flashing. the ECU is running with the new updates successfully"
                    self._logger.log_message(
                    log_type=LogType.ACKNOWLEDGMENT,
                    message=success_msg)
                    transfer_request.successfull_flashing_response(transfer_request.flashed_ecu_number)
                    transfer_request.failed_flashing_response(ecu_number=transfer_request.Flashing_Request_ID,erasing_happen=True)
            # Move operation to completed operations
            self.remove_pending_operation(operation)
            self.add_completed_operation(operation)



    def request_download(self, transfer_request: TransferRequest) -> List[int]:
        self._logger.log_message(
            log_type=LogType.DEBUG,
            message=f"{transfer_request.get_req()}Request download service message for {transfer_request.recv_DA} begin preparing"
            )
                
        if not self.check_access_required(OperationType.REQUEST_DOWNLOAD):
            error_msg = f"Error: Insufficient session level for REQUEST_DOWNLOAD. Current session: {self._session}"
            # #print(error_msg)
            self._logger.log_message(
            log_type=LogType.ERROR,
            message=error_msg)
            self.add_log(error_msg)
            return [0x00]


        # Calculate DataFormatIdentifier
        data_format_identifier = (transfer_request.compression_method.value << 4)

        # Calculate AddressAndLengthFormatIdentifier
        address_length = len(transfer_request.memory_address)
        size_length = len(str(transfer_request.data_size))
        address_length_format_identifier = (size_length << 4) | address_length
        
        # Prepare message
        message = [0x34, data_format_identifier, address_length_format_identifier]
        
        # Add memory address
        message.extend(transfer_request.memory_address)
        
        # Add memory size
        size_bytes = transfer_request.data_size.to_bytes(size_length, byteorder='big')
        message.extend(size_bytes)

        # Update transfer request and add to list
        transfer_request.status = TransferStatus.MEMORY_ERASED
        self.transfer_requests.append(transfer_request)

        log_msg = f"{transfer_request.get_req()}Created REQUEST_DOWNLOAD operation for Diagnostic address {hex(transfer_request.recv_DA)}. Message: {[hex(x) for x in message]}"
        self._logger.log_message(
            log_type=LogType.INFO,
            message=log_msg)        
        self.add_log(log_msg)
        
        return message

    def on_request_download_respond(self, message: List[int]):

        # Find transfer request with CREATED status
        transfer_request = next((req for req in self.transfer_requests 
                               if req.status == TransferStatus.MEMORY_ERASED), None)
        
        if not transfer_request:
            error_msg = "No pending transfer request found"
            self._logger.log_message(
                log_type=LogType.ERROR,
                message=error_msg
            )
            self.add_log(error_msg)
            return
        
        self._logger.log_message(
            log_type=LogType.ACKNOWLEDGMENT,
            message=f"{transfer_request.get_req()}Request download respond for {hex(transfer_request.recv_DA)} received with message : {[hex(x) for x in message]}")
        
        if message[0] == 0x74:  # Positive response
            self._logger.log_message(
            log_type=LogType.ACKNOWLEDGMENT,
            message=f"{transfer_request.get_req()}Request download respond for {hex(transfer_request.recv_DA)} is positive")

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
            message=f"{transfer_request.get_req()}Transfer data request for {hex(transfer_request.recv_DA)} sended with message : {[hex(x) for x in message]}")

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
            transfer_request.flashing_ECU_REQ.failed_flashing_response(ecu_number=transfer_request.flashing_ECU_REQ.Flashing_Request_ID,erasing_happen=True)


    def transfer_data(self, transfer_request: TransferRequest) -> List[int]:
        self._logger.log_message(
            log_type=LogType.DEBUG,
            message=f"{transfer_request.get_req()}  Transfer data service message for {hex(transfer_request.recv_DA)} begin preparing"
        )
                        
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

        log_msg = (f"{transfer_request.get_req()} Created TRANSFER_DATA message. Block: {block_sequence_counter}, "
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
            message=f"{transfer_request.get_req()} Transfer data respond for {hex(transfer_request.recv_DA)} received with message : {[hex(x) for x in message]}")
        
        if message[0] == 0x76:  # Positive response
            self._logger.log_message(
            log_type=LogType.ACKNOWLEDGMENT,
            message=f"{transfer_request.get_req()}Transfer data respond for {hex(transfer_request.recv_DA)} is postitive")
                    
            block_sequence_counter = message[1]
            
            if block_sequence_counter != transfer_request.current_number_of_steps:
                transfer_request.status = TransferStatus.REJECTED
                transfer_request.flashing_ECU_REQ.status = FlashingECUStatus.REJECTED
                transfer_request.NRC = 0x73  # Wrong Block Sequence Counter
                error_msg = f"{transfer_request.get_req() }Wrong Block Sequence Counter"
                self._logger.log_message(
                log_type=LogType.ERROR,
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
                message=f"{transfer_request.get_req()}  Request Transfer Exit for {hex(transfer_request.recv_DA)} sended with message : {[hex(x) for x in message]}")                
            else:
                message= self.transfer_data(transfer_request)
                self._logger.log_message(
                log_type=LogType.ACKNOWLEDGMENT,
                message=f"{transfer_request.get_req()} Transfer data request for {hex(transfer_request.recv_DA)} sended with message : {[hex(x) for x in message]}")                
                self.clientSend(message=message,server_can_id=self.can_id)

        elif message[0] == 0x7F:  # Negative response
            transfer_request.status = TransferStatus.REJECTED
            transfer_request.NRC = message[2]
            error_msg = f"Transfer Data Failed - NRC: {hex(transfer_request.NRC)}"
            self._logger.log_message(
            log_type=LogType.ERROR,
            message=error_msg)
            self.add_log(error_msg)
            transfer_request.flashing_ECU_REQ.failed_flashing_response(ecu_number=transfer_request.flashing_ECU_REQ.Flashing_Request_ID,erasing_happen=True)

    def request_transfer_exit(self, transfer_request: TransferRequest) -> List[int]:
        self._logger.log_message(
            log_type=LogType.DEBUG,
            message=f"{transfer_request.get_req()}  Request transfer Exit service message for {hex(transfer_request.recv_DA)} begin preparing"
        )
                               
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
        #     #print(f"crc: {crc}")
        #     message.append(crc)
        #     # message.append(crc)
        # else:
        message = [0x37]

        log_msg = f"{transfer_request.get_req()} Created REQUEST_TRANSFER_EXIT message. Checksum: {transfer_request.checksum_required}"
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
            #print(error_msg)
            self.add_log(error_msg)
            return
        self._logger.log_message(
            log_type=LogType.INFO,
            message=f"{transfer_request.get_req()} Request Transfer Exit respond for {transfer_request.recv_DA} received with message : {[hex(x) for x in message]}")
        
        if message[0] == 0x77:  # Positive response
            transfer_request.status = TransferStatus.CHECKING_CRC
            if  transfer_request.checksum_required == CheckSumMethod.NO_CHECKSUM:
                transfer_request.status = TransferStatus.CLOSED_SUCCESSFULLY
                success_msg = f"{transfer_request.get_req()} Transfer completed successfully for ECU with diagnostic address : {hex(self.can_id)}"
                self._logger.log_message(
                log_type=LogType.ACKNOWLEDGMENT,
                message=success_msg)
                self.add_log(success_msg)
                return
            else:
                
                message=self.check_memory(transfer_request)
                
                self.clientSend(message=message,server_can_id=self.can_id)
                self._logger.log_message(
                log_type=LogType.ACKNOWLEDGMENT,
                message=f"{transfer_request.get_req()}Check Memory subroutine service for {transfer_request.recv_DA} sended with message : {[hex(x) for x in message]}") 

            self.add_log(success_msg)
        
        elif message[0] == 0x7F:  # Negative response
            transfer_request.status = TransferStatus.REJECTED
            transfer_request.NRC = message[2]
            error_msg = f"Transfer Exit Failed - NRC: {hex(transfer_request.NRC)}"
            self._logger.log_message(
            log_type=LogType.ERROR,
            message=error_msg)
            self.add_log(error_msg)
            transfer_request.flashing_ECU_REQ.failed_flashing_response(ecu_number=transfer_request.flashing_ECU_REQ.Flashing_Request_ID,erasing_happen=True)

    def communication_control(self, sub_function: CommunicationControlSubFunction, 
                            control_type: CommunicationControlType) -> List[int]:
        if not self.check_access_required(OperationType.COMMUNICATION_CONTROL):
            error_msg = f"Error: Insufficient session level for COMMUNICATION_CONTROL. Current session: {self._session}"
            #print(error_msg)
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
                #print(success_msg)
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
                #print(error_msg)
                self.add_log(error_msg)

    def erase_memory(self, transfer_request: TransferRequest) -> List[int]:


        self._logger.log_message(
            log_type=LogType.DEBUG,
            message=f"{transfer_request.get_req()}  ERASE MEMORY service message for {hex(transfer_request.recv_DA)} begin preparing"
        )
        
        if not self.check_access_required(OperationType.ERASE_MEMORY):
            transfer_request.status=TransferStatus.REJECTED

            if transfer_request.is_multiple_segments == True:
                transfer_request.flashing_ECU_REQ.status=FlashingECUStatus.REJECTED

            error_msg = f"Error: Insufficient session level for ERASE_MEMORY. Current session: {self._session}"
            self._logger.log_message(
                log_type=LogType.DEBUG,
                message=f"{transfer_request.get_req()} {error_msg}"
            )
            return [0x00]
        
        memory_address=transfer_request.memory_address
        memory_size=transfer_request.data_size        
        transfer_request.status=TransferStatus.CREATED

        self.transfer_requests.append(transfer_request)      

        # Calculate AddressAndLengthFormatIdentifier
        address_length = len(transfer_request.memory_address)
        size_length = len(str(transfer_request.data_size))
        address_length_format_identifier = (size_length << 4) | address_length
        
        # Prepare message
        message = [0x31, 0x01, 0xFF, 0x00, address_length_format_identifier]
        # Add memory address
        message.extend(transfer_request.memory_address)
        
        # Add memory size
        size_bytes = transfer_request.data_size.to_bytes(size_length, byteorder='big')
        message.extend(size_bytes)
        # message.append(0x00)  # Reserved byte

        # Create and add operation
        operation = Operation(OperationType.ERASE_MEMORY, message)
        self.add_pending_operation(operation)

        log_msg = (f"Created ERASE_MEMORY operation. "
                  f"Address Length: {address_length}, "
                  f"Size Length: {size_length}, "
                  f"Address: {[hex(x) for x in memory_address]}, "
                  f"Size: { memory_size}")
        self.add_log(log_msg)
        self._logger.log_message(
            log_type=LogType.DEBUG,
            message=log_msg)        
                
        log_msg = f"{transfer_request.get_req()} Created Erase_Memory operation for Diagnostic address {transfer_request.recv_DA}. Message: {[hex(x) for x in message]}"
        self._logger.log_message(
            log_type=LogType.INFO,
            message=log_msg)        
        self.add_log(log_msg)
        return message

    def on_erase_memory_respond(self, message: List[int]):

        self._logger.log_message(
            log_type=LogType.DEBUG,
            message=f"the message received is erase memory respond . messgae:{[hex(x) for x in message]} "
        )

        transfer_request = next((req for req in self.transfer_requests 
                if req.status == TransferStatus.CREATED), None)
           
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


                transfer_request = next((req for req in self.transfer_requests 
                               if req.status == TransferStatus.CREATED), None)
            
                if  transfer_request:
                    
                    transfer_request.status=TransferStatus.MEMORY_ERASED
                    success_msg = f"{transfer_request.get_req()} Memory Erase Operation Completed Successfully for server with DA:: {self.can_id}"
                    self._logger.log_message(
                    log_type=LogType.ACKNOWLEDGMENT,
                    message=success_msg
                    )
                    message = self.request_download(transfer_request)
                    if message != [0x00]:  # Check if request was successful
                # Create address object for ISO-TP
                        self.clientSend(message=message,server_can_id=self.can_id)
                        self._logger.log_message(
                            log_type=LogType.ACKNOWLEDGMENT,
                            message=f"{transfer_request.get_req()}REQUEST download for diagnostic address {hex(self.can_id)}send successfully with messaage: {[hex(x) for x in message]}"
                        )

                      
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
                #print(error_msg)
                self.add_log(error_msg)
                
                transfer_request.flashing_ECU_REQ.failed_flashing_response(ecu_number=transfer_request.flashing_ECU_REQ.Flashing_Request_ID,erasing_happen=True)


    def check_memory(self, transfer_request: TransferRequest) -> List[int]:
        self._logger.log_message(
            log_type=LogType.DEBUG,
            message=f"{transfer_request.get_req()}  CHECK MEMORY service message for {hex(transfer_request.recv_DA)} begin preparing"
        )
        if transfer_request.status != TransferStatus.CHECKING_CRC:
            error_msg = f"Invalid transfer status for CHECK_MEMORY: {transfer_request.status}"
            #print(error_msg)
            self.add_log(error_msg)
            return [0x00]

        # Prepare base message
        message = [0x31, 0x01, 0xFF, 0x01, transfer_request.checksum_required.value]

        # Calculate and add checksum based on method
        if transfer_request.checksum_required == CheckSumMethod.CRC_16:
            checksum:bytearray=None
            if transfer_request.compression_method != CompressionMethod.NO_COMPRESSION:
                checksum = self.calculate_crc16(transfer_request.deCompressed_data)
            else:
                checksum = self.calculate_crc16(transfer_request.data)
            
            message.extend(checksum)
            
            log_msg = f"{transfer_request.get_req()}Using CRC-16 checksum: {[hex(x) for x in checksum]}"
        elif transfer_request.checksum_required == CheckSumMethod.CRC_32:
            try:
                
                checksum:bytearray=None
                if transfer_request.compression_method != CompressionMethod.NO_COMPRESSION:
                    checksum = self.calculate_crc32(transfer_request.deCompressed_data)
                else:
                    checksum = self.calculate_crc32(transfer_request.data)
                    
                message.extend(checksum)
                
                log_msg = f"{transfer_request.get_req()} Using CRC-32 checksum: {[hex(x) for x in checksum]}"
            except Exception as e:
                self._logger.log_message(
                    log_type=LogType.ERROR,
                    message=e
                )               
        else:
            log_msg = "No checksum required"
            self._logger.log_message(
                log_type=LogType.DEBUG,
                message=log_msg
            )

        self.add_log(log_msg)
        log_msg = f"{transfer_request.get_req()}Created CHECK_MEMORY operation. Message: {[hex(x) for x in message]}"
        self._logger.log_message(
            log_type=LogType.INFO,
            message=log_msg
        )
        self.add_log(log_msg)
        
        return message

    def on_check_memory_respond(self, message: List[int]):
        self._logger.log_message(
            log_type=LogType.DEBUG,
            message=f"the message received is check memory respond . messgae:{[hex(x) for x in message]} "
        )
        # Find transfer request with CHECKING_CRC status
        transfer_request = next((req for req in self.transfer_requests 
                               if req.status == TransferStatus.CHECKING_CRC), None)
        
        if not transfer_request:
            error_msg = "No transfer request in CRC checking state"
            #print(error_msg)
            self.add_log(error_msg)
            return

        if message[0] == 0x71:  # Positive response
            if (message[1] == 0x01 and 
                message[2] == 0xFF and 
                message[3] == 0x01):  # Validate routine identifier
                
                transfer_request.status = TransferStatus.CLOSED_SUCCESSFULLY
                success_msg = (f"Memory Check Success - Checksum verified using "
                             f"{transfer_request.checksum_required.name}")
                
                #print(success_msg)
                self.add_log(success_msg)
                success_msg = f"{transfer_request.get_req()} Transfer completed successfully for ECU with diagnostic address : {self.can_id}"
                self._logger.log_message(
                log_type=LogType.ACKNOWLEDGMENT,
                message=success_msg)
                self.add_log(success_msg)
                if transfer_request.is_multiple_segments == True :
                    self.handle_flashing_segments(transfer_request)
                
            
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
            #print(error_msg)
            self.add_log(error_msg)
            transfer_request.flashing_ECU_REQ.failed_flashing_response(ecu_number=transfer_request.flashing_ECU_REQ.Flashing_Request_ID,erasing_happen=True)
            
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
    
    def handle_flashing_segments(self,transfer_request:TransferRequest):
        if transfer_request.status == TransferStatus.CLOSED_SUCCESSFULLY:
            flashing_ECU_Request = next((req for req in self.Flash_ECU_Segments_Request
            if req.status != FlashingECUStatus.REJECTED or req.status == FlashingECUStatus.RESET), None)

            if flashing_ECU_Request:
                if flashing_ECU_Request.status == FlashingECUStatus.SENDING_FIRST_SEGMENT or flashing_ECU_Request.status ==FlashingECUStatus.SENDING_CONSECUTIVE_SEGMENTS:
                    flashing_ECU_Request.current_number_of_segments_send+=1
                    if flashing_ECU_Request.current_number_of_segments_send == flashing_ECU_Request.number_of_segments:
                        flashing_ECU_Request.status=FlashingECUStatus.COMPLETED
                        self._logger.log_message(
                        log_type=LogType.ACKNOWLEDGMENT,
                        message=f"{flashing_ECU_Request.get_req()} Flashing ECU REQUEST had sent all segments successfully")
                        validationMessage=self.finalize_programming(flashing_ECU_Request=flashing_ECU_Request)
                        #print("reg3 mnha")
                        if validationMessage != [0x00]:
                            self.clientSend(message=validationMessage,server_can_id=self.can_id)
                            #print("3aml send ll message")
                            self._logger.log_message(
                            log_type=LogType.ACKNOWLEDGMENT,
                            message=f"{flashing_ECU_Request.get_req()} Flashing ECU REQUEST had sent routine control finalize programming with message {[hex(x) for x in validationMessage]}")
                            flashing_ECU_Request.status=FlashingECUStatus.VALIDATING_ENCRYP
                        #make authenticity
                        #reset the ECU
                    elif flashing_ECU_Request.current_number_of_segments_send < flashing_ECU_Request.number_of_segments:
                        flashing_ECU_Request.status=FlashingECUStatus.SENDING_CONSECUTIVE_SEGMENTS
                        self._logger.log_message(
                        log_type=LogType.ACKNOWLEDGMENT,
                        message=f"{flashing_ECU_Request.get_req()} Flashing ECU REQUEST had sent Segment number: {flashing_ECU_Request.current_number_of_segments_send-1} successfully")
                        self.client_Segment_send(recv_DA=flashing_ECU_Request.recv_DA,
                                        data=flashing_ECU_Request.segments[flashing_ECU_Request.current_number_of_segments_send].data,
                                        memory_address=flashing_ECU_Request.segments[flashing_ECU_Request.current_number_of_segments_send].address,
                                        checksum_required=flashing_ECU_Request.checksum_required,
                                        encryption_method=flashing_ECU_Request.encryption_method,
                                        compression_method=flashing_ECU_Request.compression_method,
                                        is_multiple_segments=True,
                                        flashing_ECU_req=flashing_ECU_Request
                                        )
                                                
    def finalize_programming(self,flashing_ECU_Request:FlashingECU ) -> List[int]:
        self._logger.log_message(
            log_type=LogType.DEBUG,
            message=f"{flashing_ECU_Request.get_req()}  Finalize programming routine control message for {hex(flashing_ECU_Request.recv_DA)} begin preparing"
        )

        if flashing_ECU_Request.status != FlashingECUStatus.COMPLETED:
            error_msg = f"Invalid flashing status for finalize_programming: {flashing_ECU_Request.status}"
            self._logger.log_message(
                log_type=LogType.ERROR,
                message=error_msg
            )
            return [0x00]
        
        
        # Prepare base message
        message = [0x31, 0x01, 0xFF, 0x02,flashing_ECU_Request.encryption_method.value]


        # Calculate and add checksum based on method
        if flashing_ECU_Request.encryption_method == EncryptionMethod.SEC_P_256_R1:
            alldata = bytearray()
            for x in flashing_ECU_Request.segments:
                self._logger.log_message(
                    log_type=LogType.INFO,
                    message=f"length : {len(x.data)}"
                )
                alldata.extend(x.data)
            #print(alldata)
            #print(type(alldata))
            # Create ECDSA manager instance
            ecdsa = ECDSAManager()
            
            
            
            

            signature, status = ecdsa.sign_message(bytearray(alldata))
            if status != 0:
                error_msg=f"{flashing_ECU_Request.get_req()} ERROR: Signing failed with status: {status}"
                self._logger.log_message(
                    log_type=LogType.ERROR,
                    message=error_msg
                )
                return [0x00]
        
            msg=f"Signature Type:     {type(signature)}"
            self._logger.log_message(
                    log_type=LogType.INFO,
                    message=msg
                )
            msg=f"Signature Length:   {len(signature)} bytes"
            self._logger.log_message(
                    log_type=LogType.INFO,
                    message=msg
                )
            msg=f"Signature (hex):    {signature.hex()}"
            self._logger.log_message(
                    log_type=LogType.INFO,
                    message=msg
                )        
            msg=f"  First 32 bytes (r):  {signature[:32].hex()}"
            self._logger.log_message(
                    log_type=LogType.INFO,
                    message=msg
                )        
            msg=f"  Last 32 bytes (s):   {signature[32:].hex()}"
            self._logger.log_message(
                    log_type=LogType.INFO,
                    message=msg
                )
            
            message.extend(signature)
        elif flashing_ECU_Request.encryption_method == EncryptionMethod.NO_ENCRYPTION:
            
            message.append(0x00)
            #print(message)        
        else:
            log_msg = "Invalid Encryption method specified "
            self._logger.log_message(
                log_type=LogType.ERROR,
                message=log_msg
            )



        log_msg = f"{flashing_ECU_Request.get_req()} Created finalize programming Routine control for ECU with DA:{hex(flashing_ECU_Request.recv_DA)}. Message: {[hex(x) for x in message]}"

        self._logger.log_message(
        log_type=LogType.ACKNOWLEDGMENT,
        message=log_msg)

    
        return message

    def on_finalize_programming_respond(self, message: List[int]):
        self._logger.log_message(
            log_type=LogType.DEBUG,
            message=f"the message received is finalize programming routine control respond . messgae:{[hex(x) for x in message]} "
        )
        # Find transfer request with CHECKING_CRC status
        flashing_ecu_req = next((req for req in self.Flash_ECU_Segments_Request 
                               if req.status == FlashingECUStatus.VALIDATING_ENCRYP), None)
        
        if not flashing_ecu_req:
            error_msg = "No flashing ECU in validating encryption state"
            #print(error_msg)
            self.add_log(error_msg)
            return

        if message[0] == 0x71:
            try:  # Positive response
                if (message[1] == 0x01 and 
                    message[2] == 0xFF and 
                    message[3] == 0x02):  # Validate routine identifier
                    
                    flashing_ecu_req.status = FlashingECUStatus.CLOSED_SUCCESSFULLY
                    success_msg = (f"{flashing_ecu_req.get_req()}Finalize programming Success - Flashing verified ")
                    self._logger.log_message(
                        log_type=LogType.ACKNOWLEDGMENT,
                        message=success_msg
                    )
                    #print(success_msg)
                    self.add_log(success_msg)
                    success_msg = f"{flashing_ecu_req.get_req()} Flashing completed successfully for ECU with diagnostic address : {self.can_id}"
                    self._logger.log_message(
                    log_type=LogType.ACKNOWLEDGMENT,
                    message=success_msg)
                    self.add_log(success_msg)
                    message=self.ecu_reset(reset_type=0X01)
                    if message !=0x0:
                        flashing_ecu_req.successfull_flashing_response(0)
                        self.clientSend(message=message,server_can_id=self.can_id)
                        success_msg = f"{flashing_ecu_req.get_req()} HARD RESET SERVICE for ECU with diagnostic address : {self.can_id} send successfully"
                        self._logger.log_message(
                        log_type=LogType.ACKNOWLEDGMENT,
                        message=success_msg)
                    
            except Exception as e:
                self._logger.log_message(
                    log_type=LogType.ERROR,
                    message=e
                )    
                
        elif message[0] == 0x7F:  # Negative response
            flashing_ecu_req.status = TransferStatus.REJECTED
            flashing_ecu_req.NRC = message[2]
            
            nrc_descriptions = {
            0x10: "General Reject", # 0x10
            0x11: "Service Not Supported", # 0x11
            0x12: "Sub-Function Not Supported", # 0x12
            0x13: "Incorrect Message Length / Format", # 0x13
            0x22: "Conditions Not Correct", # 0x22 (e.g., voltage, session, etc.)
            0x24: "Request Sequence Error", # 0x24
            0x31: "Request Out Of Range", # 0x31 (e.g., invalid routine ID, bad parameters)
            0x33: "Security Access Denied", # 0x33 (not unlocked at correct security level)
            0x36: "Exceed Number Of Attempts", # 0x36 (e.g., too many wrong signatures)
            0x37: "Required Time Delay Not Expired", # 0x37
            0x72: "General Programming Failure" # 0x72 (covers generic flash/verification fail)
            }
            
            error_msg = (f"Memory Check Failed - NRC: {hex(flashing_ecu_req.NRC)} - "
                        f"{nrc_descriptions.get(flashing_ecu_req.NRC, 'Unknown Error')}")
            #print(error_msg)
            self.add_log(error_msg)
            flashing_ecu_req.failed_flashing_response(ecu_number=flashing_ecu_req.Flashing_Request_ID,erasing_happen=True) 

# def calculate_crc32(data: bytearray) -> bytearray:
#     crc = zlib.crc32(data) & 0xFFFFFFFF
#     return crc.to_bytes(4, byteorder='big')
# data=[0x52, 0x55, 0x32]
# data=bytearray(data)
# #print(data)
# checksu=calculate_crc32(data=data)  
# #print(checksu)
# data.extend(checksu)
# #print(data)
    def security_access(self, transfer_request: TransferRequest, security_level: int) -> List[int]:
        """
        Prepare security access request seed message
        
        Args:
            transfer_request: The transfer request object
            security_level: The security level (1, 2, 3, etc.)
        
        Returns:
            List[int]: UDS message for requesting seed
        """
        self._logger.log_message(
            log_type=LogType.DEBUG,
            message=f"{transfer_request.get_req()}Security access request seed for level {security_level} for {transfer_request.recv_DA} begin preparing"
        )
        
        # Check if operation is allowed in current session
        if not self.check_access_required(OperationType.SECURITY_ACCESS):
            error_msg = f"Error: Insufficient session level for SECURITY_ACCESS. Current session: {self._session}"
            self._logger.log_message(
                log_type=LogType.ERROR,
                message=error_msg
            )
            self.add_log(error_msg)
            return [0x00]
        
        # Calculate sub-function for request seed (odd values)
        sub_function = (security_level * 2) - 1  # Level 1=0x01, Level 2=0x03, Level 3=0x05, etc.
        
        # Prepare message: Service ID + Sub-function
        message = [0x27, sub_function]
        
        # Update transfer request status
        transfer_request.status = TransferStatus.REQUESTING_SEED
        transfer_request.security_level = security_level
        
        log_msg = f"{transfer_request.get_req()}Created SECURITY_ACCESS request seed for level {security_level}, Diagnostic address {hex(transfer_request.recv_DA)}. Message: {[hex(x) for x in message]}"
        self._logger.log_message(
            log_type=LogType.INFO,
            message=log_msg
        )
        self.add_log(log_msg)
        
        return message


    def on_security_access_request_seed_respond(self, message: List[int]):
        """
        Handle security access request seed response
        
        Args:
            message: Response message from ECU
        """
        # Find transfer request with REQUESTING_SEED status
        transfer_request = next((req for req in self.transfer_requests 
                            if req.status == TransferStatus.REQUESTING_SEED), None)
        
        if not transfer_request:
            error_msg = "No pending security access request found"
            self._logger.log_message(
                log_type=LogType.ERROR,
                message=error_msg
            )
            self.add_log(error_msg)
            return
        
        self._logger.log_message(
            log_type=LogType.ACKNOWLEDGMENT,
            message=f"{transfer_request.get_req()}Security access request seed respond for {hex(transfer_request.recv_DA)} received with message: {[hex(x) for x in message]}"
        )
        
        if message[0] == 0x67:  # Positive response
            self._logger.log_message(
                log_type=LogType.ACKNOWLEDGMENT,
                message=f"{transfer_request.get_req()}Security access request seed respond for {hex(transfer_request.recv_DA)} is positive"
            )
            
            # Extract seed from response (skip service ID and sub-function)
            seed_bytes = message[2:]
            
            # Check if seed is all zeros (already unlocked)
            if all(byte == 0 for byte in seed_bytes):
                self._logger.log_message(
                    log_type=LogType.INFO,
                    message=f"{transfer_request.get_req()}Security level {transfer_request.security_level} already unlocked for {hex(transfer_request.recv_DA)}"
                )
                
                # Security already unlocked, proceed to erase memory
                message = self.erase_memory(transfer_request)
                if message != [0x00]:  # Check if request was successful
                    self.clientSend(message=message, server_can_id=self.can_id)
                    self._logger.log_message(
                        log_type=LogType.ACKNOWLEDGMENT,
                        message=f"{transfer_request.get_req()} ERASE memory for diagnostic address {hex(transfer_request.recv_DA)} send successfully with message: {[hex(x) for x in message]}"
                    )
            else:
                # Generate key from seed using recommended algorithm
                # Convert seed bytes to 32-bit integer
                if len(seed_bytes) >= 4:
                    seed = int.from_bytes(seed_bytes[:4], 'big')
                else:
                    # Pad with zeros if seed is less than 4 bytes
                    seed_padded = seed_bytes + [0] * (4 - len(seed_bytes))
                    seed = int.from_bytes(seed_padded, 'big')
                
                # Generate key using recommended algorithm
                key = self.generate_recommended_key(seed, transfer_request.security_level)
                
                # Convert key back to bytes
                key_bytes = key.to_bytes(4, 'big')
                
                # Prepare send key message
                # Sub-function for send key (even values)
                sub_function = transfer_request.security_level * 2  # Level 1=0x02, Level 2=0x04, Level 3=0x06, etc.
                
                # Create send key message
                send_key_message = [0x27, sub_function]
                send_key_message.extend(key_bytes)
                
                # Update status
                transfer_request.status = TransferStatus.SENDING_KEY
                
                # Send key message
                self.clientSend(message=send_key_message, server_can_id=self.can_id)
                self._logger.log_message(
                    log_type=LogType.ACKNOWLEDGMENT,
                    message=f"{transfer_request.get_req()}Security access send key for {hex(transfer_request.recv_DA)} sent with message: {[hex(x) for x in send_key_message]}"
                )
        
        elif message[0] == 0x7F and message[1] == 0x27:  # Negative response
            self._logger.log_message(
                log_type=LogType.INFO,
                message=f"Security access request seed respond for {transfer_request.recv_DA} is negative"
            )
            
            transfer_request.NRC = message[2]
            transfer_request.status = TransferStatus.REJECTED
            
            nrc_descriptions = {
                0x10: "General Reject",
                0x11: "Service Not Supported",
                0x12: "Sub-Function Not Supported",
                0x13: "Invalid Message Length Or Invalid Format",
                0x22: "Conditions Not Correct",
                0x24: "Request Sequence Error",
                0x31: "Request Out Of Range",
                0x36: "Exceeded Number Of Attempts",
                0x37: "Required Time Delay Not Expired"
            }
            
            error_msg = f"Security Access Request Seed Failed - NRC: {hex(transfer_request.NRC)} - {nrc_descriptions.get(transfer_request.NRC, 'Unknown Error')}"
            self._logger.log_message(
                log_type=LogType.ERROR,
                message=error_msg
            )
            self.add_log(error_msg)
            transfer_request.flashing_ECU_REQ.failed_flashing_response(
                ecu_number=transfer_request.flashing_ECU_REQ.Flashing_Request_ID,
                erasing_happen=False
            )


    def on_security_access_send_key_respond(self, message: List[int]):
        """
        Handle security access send key response
        
        Args:
            message: Response message from ECU
        """
        # Find transfer request with SENDING_KEY status
        transfer_request = next((req for req in self.transfer_requests 
                            if req.status == TransferStatus.SENDING_KEY), None)
        
        if not transfer_request:
            error_msg = "No pending security access send key found"
            self._logger.log_message(
                log_type=LogType.ERROR,
                message=error_msg
            )
            self.add_log(error_msg)
            return
        
        self._logger.log_message(
            log_type=LogType.ACKNOWLEDGMENT,
            message=f"{transfer_request.get_req()}Security access send key respond for {hex(transfer_request.recv_DA)} received with message: {[hex(x) for x in message]}"
        )
        
        if message[0] == 0x67:  # Positive response
            self._logger.log_message(
                log_type=LogType.ACKNOWLEDGMENT,
                message=f"{transfer_request.get_req()}Security access send key respond for {hex(transfer_request.recv_DA)} is positive"
            )
            
            # Security access successful, proceed to erase memory
            message = self.erase_memory(transfer_request)
            if message != [0x00]:  # Check if request was successful
                self.clientSend(message=message, server_can_id=self.can_id)
                self._logger.log_message(
                    log_type=LogType.ACKNOWLEDGMENT,
                    message=f"{transfer_request.get_req()} ERASE memory for diagnostic address {hex(transfer_request.recv_DA)} send successfully with message: {[hex(x) for x in message]}"
                )
        
        elif message[0] == 0x7F and message[1] == 0x27:  # Negative response
            self._logger.log_message(
                log_type=LogType.INFO,
                message=f"Security access send key respond for {transfer_request.recv_DA} is negative"
            )
            
            transfer_request.NRC = message[2]
            transfer_request.status = TransferStatus.REJECTED
            
            nrc_descriptions = {
                0x10: "General Reject",
                0x11: "Service Not Supported",
                0x12: "Sub-Function Not Supported",
                0x13: "Invalid Message Length Or Invalid Format",
                0x22: "Conditions Not Correct",
                0x24: "Request Sequence Error",
                0x31: "Request Out Of Range",
                0x35: "Invalid Key",
                0x36: "Exceeded Number Of Attempts",
                0x37: "Required Time Delay Not Expired"
            }
            
            error_msg = f"Security Access Send Key Failed - NRC: {hex(transfer_request.NRC)} - {nrc_descriptions.get(transfer_request.NRC, 'Unknown Error')}"
            self._logger.log_message(
                log_type=LogType.ERROR,
                message=error_msg
            )
            self.add_log(error_msg)
            transfer_request.flashing_ECU_REQ.failed_flashing_response(
                ecu_number=transfer_request.flashing_ECU_REQ.Flashing_Request_ID,
                erasing_happen=False
            )


    def generate_recommended_key(self, seed: int, security_level: int) -> int:
        """
        Generate key using recommended algorithm
        
        Args:
            seed: The seed value received from ECU
            security_level: The security level (1, 2, 3, etc.)
        
        Returns:
            int: Generated key
        """
        # Level-specific masks
        level_masks = {
            1: 0x5A5A5A5A,  # Level 1
            2: 0xA5A5A5A5,  # Level 2
            3: 0x12345678,  # Level 3 (programming)
            4: 0x87654321   # Level 4+
        }
        
        # Get mask for the security level (default to level 1 mask if not found)
        mask = level_masks.get(security_level, level_masks[1])
        
        key = seed
        
        # 1. Bit rotation based on level
        rotation = (security_level * 3) % 32
        key = ((key << rotation) | (key >> (32 - rotation))) & 0xFFFFFFFF
        
        # 2. XOR with level-specific mask
        key ^= mask
        
        # 3. Simple scrambling
        key = ((key & 0xAAAAAAAA) >> 1) | ((key & 0x55555555) << 1)
        
        # 4. Final XOR with inverted seed
        key ^= (~seed & 0xFFFFFFFF)
        
        return key & 0xFFFFFFFF