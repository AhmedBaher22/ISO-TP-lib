# server.py
from typing import List, Optional
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from uds_layer.uds_enums import SessionType, OperationType, OperationStatus
from uds_layer.operation import Operation

class Server:
    def __init__(self, can_id: int):
        self._can_id = can_id
        self._session = SessionType.NONE
        self._pending_operations: List[Operation] = []
        self._completed_operations: List[Operation] = []
        self._logs: List[str] = []
        self._p2_timing = 0
        self._p2_star_timing = 0

    # Getters and setters
    @property
    def can_id(self) -> int:
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

    def read_data_by_identifier(self, vin: str) -> List[int]:
        if not self.check_access_required(OperationType.READ_DATA_BY_IDENTIFIER):
            error_msg = f"Error: Insufficient session level for READ_DATA_BY_IDENTIFIER. Current session: {self._session}"
            print(error_msg)
            self.add_log(error_msg)
            return [0x00]

        message = [0x22, 0xF1, 0x90]  # Request for VIN (F190)
        operation = Operation(OperationType.READ_DATA_BY_IDENTIFIER, message)
        self.add_pending_operation(operation)
        
        log_msg = f"Created READ_DATA_BY_IDENTIFIER operation for VIN. Message: {[hex(x) for x in message]}"
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

    def write_data_by_identifier(self, vin: str, data: List[int]) -> List[int]:
        if not self.check_access_required(OperationType.WRITE_DATA_BY_IDENTIFIER):
            error_msg = f"Error: Insufficient session level for WRITE_DATA_BY_IDENTIFIER. Current session: {self._session}"
            print(error_msg)
            self.add_log(error_msg)
            return [0x00]

        # Prepare message: service ID (2E) + VIN identifier (F190) + data
        message = [0x2E, 0xF1, 0x90] + data
        
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

    def request_download(self):
        pass

    def request_transfer_exit(self):
        pass