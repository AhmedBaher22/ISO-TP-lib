# uds_client.py

from bitarray import bitarray
from typing import Callable, List, Optional
from server import Server
from operation import Operation
from uds_enums import SessionType, OperationStatus, OperationType

class Address:
    def __init__(self, addressing_mode: int = 0, txid: Optional[int] = None, rxid: Optional[int] = None):
        self.addressing_mode = addressing_mode
        self._txid = txid
        self._rxid = rxid

class UdsClient:
    def __init__(self, client_id: int):
        self._client_id = client_id
        self._servers: List[Server] = []
        self._pending_servers: List[Server] = []
        self._isotp_send: Callable = None
    def set_isotp_send(self,e:Callable):
        self._isotp_send=e
    def add_server(self, address: Address, session_type: SessionType):
        # Prepare Diagnostic Session Control message (0x10)
        message = bytearray([0x10, session_type.value])
        
        # Send via ISO-TP
        self.send_message(address._txid,message)
        
        # Create new server and add to pending
        server = Server(address._rxid)
        self._pending_servers.append(server)

    def process_message(self, address: Address, data: List[int]):
        service_id = data[0]
        
        if service_id == 0x7F:  # Negative response
            requested_service = data[1]
            
            if requested_service == 0x10:  # Session Control
                server = self._find_server_by_can_id(address._txid, self._pending_servers)
                if server:
                    server.add_log(f"Session Control Negative response: {hex(data[2])}")
                    server.session = SessionType.NONE
                    self._servers.append(server)
                    self._pending_servers.remove(server)
                    
            elif requested_service == 0x22:  # Read Data By Identifier
                server = self._find_server_by_can_id(address._txid, self._servers)
                if server:
                    operation = server.get_pending_operation_by_type(OperationType.READ_DATA_BY_IDENTIFIER)
                    if operation:
                        operation.status = OperationStatus.REJECTED
                        server.remove_pending_operation(operation)
                        server.add_completed_operation(operation)
                        server.on_read_data_by_identifier_respond(0x7F, [data[2]])

            elif requested_service == 0x2E:  # Write Data By Identifier
                server = self._find_server_by_can_id(address._txid, self._servers)
                if server:
                    server.on_write_data_by_identifier_respond(0x7F, [data[2]], None)

            elif requested_service == 0x11:  # ECU Reset
                server = self._find_server_by_can_id(address._txid, self._servers)
                if server:
                    server.on_ecu_reset_respond(0x7F, [data[2]], None)
                        
        elif service_id == 0x62:  # Positive response to Read Data By Identifier
            server = self._find_server_by_can_id(address._txid, self._servers)
            if server:
                operation = server.get_pending_operation_by_type(OperationType.READ_DATA_BY_IDENTIFIER)
                if operation:
                    operation.status = OperationStatus.COMPLETED
                    server.remove_pending_operation(operation)
                    server.add_completed_operation(operation)
                    response_data = data[1:]
                    server.on_read_data_by_identifier_respond(0x62, response_data, self._extract_vin(response_data))

        elif service_id == 0x6E:  # Positive response to Write Data By Identifier
            server = self._find_server_by_can_id(address._txid, self._servers)
            if server:
                operation = server.get_pending_operation_by_type(OperationType.WRITE_DATA_BY_IDENTIFIER)
                if operation:
                    # Extract VIN from the original write request (assuming it's stored in operation.message)
                    vin = self._extract_vin(operation.message[3:])  # Skip service ID and identifier
                    server.on_write_data_by_identifier_respond(0x6E, data[1:], vin)
                    
        elif service_id == 0x51:  # Positive response to ECU Reset
            server = self._find_server_by_can_id(address._txid, self._servers)
            if server:
                operation = server.get_pending_operation_by_type(OperationType.ECU_RESET)
                if operation:
                    # Extract reset type from the original request
                    reset_type = operation.message[1]
                    # Pass any additional data (like power down time) in the message
                    server.on_ecu_reset_respond(0x51, data[1:], reset_type)
                    
        elif service_id == 0x50:  # Positive response to Session Control
            server = self._find_server_by_can_id(address._txid, self._pending_servers)
            if server:
                server.session = SessionType(data[1])
                # Set timing parameters
                if len(data) >= 6:  # Ensure we have enough bytes for timing parameters
                    server.p2_timing = (data[2] << 8) | data[3]  # Combine third and fourth bytes
                    server.p2_star_timing = (data[4] << 8) | data[5]  # Combine fifth and sixth bytes
                self._servers.append(server)
                self._pending_servers.remove(server)

    def _extract_vin(self, data: List[int]) -> str:
        try:
            return ''.join(chr(x) for x in data)
        except:
            return "Invalid VIN data"

    def _find_server_by_can_id(self, can_id: int, server_list: List[Server]) -> Optional[Server]:
        for server in server_list:
            if server.can_id == can_id:
                return server
        return None

    def _find_pending_operation(self, server: Server, service_id: int) -> Optional[Operation]:
        # Implementation depends on how you want to match service IDs to operations
        pass
    def bitarray_to_bytearray(self,bits: bitarray) -> bytearray:
        # Convert the bitarray to bytes and then to bytearray
        return bytearray(bits.tobytes())
    def receive_message(self, data: bitarray, address: Address):
        data=self.bitarray_to_bytearray(data)
        self.process_message(address, data)

    def send_message(self, server_can_id: int, message: List[int]):
        address = Address(addressing_mode=0, txid=self._client_id, rxid=server_can_id)
        
        if len(message) <= 4095:
            self._isotp_send(message, address,self.on_success_send, self.on_fail_send)
        else:
            # Split message into chunks of 4095 bytes
            for i in range(0, len(message), 4095):
                chunk = message[i:i + 4095]
                self._isotp_send(chunk, address,self.on_success_send, self.on_fail_send)

    def on_success_send(self):
        pass
    def on_fail_send(self, e:Exception):
        pass
    def on_fail_receive(self, e:Exception):
        print(e)

    def get_client_id(self):
        return self._client_id