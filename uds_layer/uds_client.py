from bitarray import bitarray
from typing import Callable, List, Optional
import sys
import os
from uds_layer.transfer_enums import TransferStatus, EncryptionMethod, CompressionMethod
from uds_layer.transfer_request import TransferRequest
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from uds_layer.server import Server
from uds_layer.operation import Operation
from uds_layer.uds_enums import SessionType, OperationStatus, OperationType
from logger import Logger, LogType


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
        self.logger = Logger("uds")

    def set_isotp_send(self, e: Callable):
        self._isotp_send = e

    def get_servers(self):
        return self._servers

    def get_pending_servers(self):
        return self._pending_servers

    def add_server(self, address: Address, session_type: SessionType):
        # Prepare Diagnostic Session Control message (0x10)
        message = bytearray([0x10, session_type.value])

        # Send via ISO-TP
        self.send_message(address._txid, message)

        # Create new server and add to pending
        server = Server(address._rxid,client_send=self.send_message)

        self._pending_servers.append(server)
        self.logger.log_message(
            log_type=LogType.ACKNOWLEDGMENT,
            message=f"Server {address._rxid} Added successfully")

    def process_message(self, address: Address, data: bytearray):
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
            elif requested_service == 0x31:  # Erase Memory
                server = self._find_server_by_can_id(address._txid, self._servers)
                if server:
                    server.on_erase_memory_respond(data)                    
            elif requested_service == 0x28:  # Communication Control
                server = self._find_server_by_can_id(address._txid, self._servers)
                if server:
                    server.on_communication_control_respond(data)
            elif requested_service == 0x34:  # Negative response to Request Download
                server = self._find_server_by_can_id(address._txid, self._servers)
                if server:
                    server.on_request_download_respond(data)

            elif requested_service == 0x36:  # Transfer Data
                server = self._find_server_by_can_id(address._txid, self._servers)
                if server:
                    server.on_transfer_data_respond(data)
                    
            elif requested_service == 0x37:  # Request Transfer Exit
                server = self._find_server_by_can_id(address._txid, self._servers)
                if server:
                    server.on_request_transfer_exit_respond(data)

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
        elif service_id == 0x74:  # Positive response to Request Download
            server = self._find_server_by_can_id(address._txid, self._servers)
            if server:
                server.on_request_download_respond(data)
                
        elif service_id == 0x76:  # Positive response to Transfer Data
            server = self._find_server_by_can_id(address._txid, self._servers)
            if server:
                server.on_transfer_data_respond(data)

        elif service_id == 0x68:  # Positive response to Communication Control
            server = self._find_server_by_can_id(address._txid, self._servers)
            if server:
                server.on_communication_control_respond(data)    

        elif service_id == 0x77:  # Positive response to Request Transfer Exit
            server = self._find_server_by_can_id(address._txid, self._servers)
            if server:
                server.on_request_transfer_exit_respond(data)
                
        elif service_id == 0x71:  # Positive response to Erase Memory
            server = self._find_server_by_can_id(address._txid, self._servers)
            if server:
                server.on_erase_memory_respond(data)                                    
        elif service_id == 0x74:  # Positive response to Request Download
            server = self._find_server_by_can_id(address._txid, self._servers)
            if server:
                server.on_request_download_respond(data)
        elif service_id == 0x62:  # Positive response to Read Data By Identifier

            server = self._find_server_by_can_id(address._txid, self._servers)
            if server:

                operation = server.get_pending_operation_by_type(OperationType.READ_DATA_BY_IDENTIFIER)
                if operation:

                    # operation.status = OperationStatus.COMPLETED
                    # server.remove_pending_operation(operation)
                    # server.add_completed_operation(operation)
                    response_data = data[3:]
                    server.on_read_data_by_identifier_respond(0x62, response_data, data[1:3])

        elif service_id == 0x6E:  # Positive response to Write Data By Identifier
            server = self._find_server_by_can_id(address._txid, self._servers)
            if server:
                operation = server.get_pending_operation_by_type(OperationType.WRITE_DATA_BY_IDENTIFIER)
                if operation:
                    # Extract VIN from the original write request (assuming it's stored in operation.message)
                    vin = operation.message[1:3]  # Skip service ID and identifier
                    server.on_write_data_by_identifier_respond(0x6E, data[1:3], vin)

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
                print("Gained control session ",server.session," with timings:: ", "P2 timing", server.p2_timing, "P2 star timing", server.p2_star_timing )



    def _find_server_by_can_id(self, can_id: [int], server_list: List[Server]) -> Optional[Server]:
        for server in server_list:
            if server.can_id == can_id:
                return server
        return None

    def _find_pending_operation(self, server: Server, service_id: int) -> Optional[Operation]:
        # Implementation depends on how you want to match service IDs to operations
        pass

    def bitarray_to_bytearray(self, bits: bitarray) -> bytearray:
        # Convert the bitarray to bytes and then to bytearray
        return bytearray(bits.tobytes())

    def receive_message(self, data: bitarray, address: Address):
        data = data.tobytes()
        self.process_message(address, data)
        self.logger.log_message(
            log_type=LogType.ACKNOWLEDGMENT,
            message=f"Message {data} received successfully")

    def send_message(self, server_can_id: int, message: List[int]):
        address = Address(addressing_mode=0, txid=self._client_id, rxid=server_can_id)

        if len(message) <= 4095:
            self._isotp_send(message, address, self.on_success_send, self.on_fail_send)
        else:
            # Split message into chunks of 4095 bytes
            for i in range(0, len(message), 4095):
                chunk = message[i:i + 4095]
                self._isotp_send(chunk, address, self.on_success_send, self.on_fail_send)

        self.logger.log_message(
            log_type=LogType.ACKNOWLEDGMENT,
            message=f"Message {message} sent successfully")

    def on_success_send(self):
        pass

    def on_fail_send(self, e: Exception):
        pass

    def on_fail_receive(self, e: Exception):
        print(e)

    def get_client_id(self):
        return self._client_id
    
    def transfer_NEW_data_to_ecu(self, recv_DA: int, data: bytearray, 
                                encryption_method: EncryptionMethod,
                                compression_method: CompressionMethod,
                                memory_address: bytearray,
                                checksum_required: bool) -> None:
        # Create TransferRequest object
        transfer_request = TransferRequest(
            recv_DA=recv_DA,
            data=data,
            encryption_method=encryption_method,
            compression_method=compression_method,
            memory_address=memory_address,
            checksum_required=checksum_required
        )

        # Find server with matching CAN ID
        server = next((s for s in self._servers if s.can_id == recv_DA), None)
        if server:
            # Get request download message
            message = server.request_download(transfer_request)
            if message != [0x00]:  # Check if request was successful
                # Create address object for ISO-TP
                address = Address(addressing_mode=0, txid=self._client_id, rxid=recv_DA)
                self.logger.log_message(
                    log_type=LogType.ACKNOWLEDGMENT,
                    message=f"request donwload for diagnostic address {recv_DA}send successfully with messaage: {message}"
                )
                # Send message using ISO-TP
                self._isotp_send(message, address,self.on_success_send,self.on_fail_send)
        else:
            self.logger.log_message(
                log_type=LogType.ERROR,
                message=f"Error: No server found to send request download  with CAN ID: {hex(recv_DA)} , please add server and open to it required session control"
            )            
