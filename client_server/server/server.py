import socket
import threading
import time
from typing import Dict, List, Optional
from datetime import datetime
import logging
from models import *
from protocol import Protocol
from database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)

class ECUUpdateServer:
    def __init__(self, host: str, port: int, data_directory: str):
        self.host = host
        self.port = port
        self.db_manager = DatabaseManager(data_directory)
        self.car_types: List[CarType] = []
        self.active_requests: Dict[str, Request] = {}  # car_id -> Request
        self.active_downloads: Dict[str, DownloadRequest] = {}  # car_id -> DownloadRequest
        self.chunk_size = 8192  # 8KB chunks for file transfer
        self.socket = None
        self.running = False

    def start(self):
        """Start the server"""
        try:
            # Load database
            self.car_types = self.db_manager.load_all_data()
            if not self.car_types:
                raise Exception("Failed to load car types database")

            # Create and bind socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True

            logging.info(f"Server started on {self.host}:{self.port}")
            
            # Start accepting connections
            while self.running:
                try:
                    client_socket, (client_ip, client_port) = self.socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_ip, client_port)
                    )
                    client_thread.daemon = True
                    logging.info(f"new socket communication received from ip: {str(client_ip)} , port number: {str(client_port)}")
                    client_thread.start()
                except Exception as e:
                    if self.running:
                        logging.error(f"Error accepting connection: {str(e)}")

        except Exception as e:
            logging.error(f"Failed to start server: {str(e)}")
            self.shutdown()

    def receive_requests(self):
        """Main loop to receive client connections"""
        while self.running:
            try:
                client_socket, (client_ip, client_port) = self.socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_ip, client_port)
                )
                client_thread.start()
            except Exception as e:
                logging.error(f"Error accepting connection: {str(e)}")

    def handle_client(self, client_socket: socket.socket, client_ip: str, client_port: int):
        """Handle individual client connection"""
        try:
            logging.info(f"starting new thread handling request from client ip:{client_ip} and port {client_port}")
            client_socket.settimeout(1000)  # Set timeout for client operations
            
            # Receive initial message
            message = self.receive_message(client_socket)

            if not message:
                logging.error(f"No initial message received from {client_ip}:{client_port}")
                return
            
            logging.info(f"received new message from client ip: {client_ip} , message:: {str(message)}")  

            if message['type'] != Protocol.HANDSHAKE:
                logging.error(f"Invalid initial message type from {client_ip}:{client_port}")
                client_socket.send(Protocol.create_error_message(400, "Invalid initial message"))
                return

            # Extract client information
            payload = message['payload']
            car_type = payload.get('car_type')
            car_id = payload.get('car_id')

            if not car_type or not car_id:
                logging.error(f"Missing required information in handshake from {client_ip}:{client_port}")
                client_socket.send(Protocol.create_error_message(400, "Missing required information"))
                return
            
            logging.info(f"client ip: {client_ip} is a car with car ID: {car_id} and car_type: {car_type}")

            service_type = ServiceType(payload['service_type'])

            logging.info(f"client ip: {client_ip} is a car with car ID: {car_id} and car_type: {car_type}. service needed:: {service_type}")

            # Create request object
            request = Request(
                timestamp=datetime.now(),
                car_type=car_type,
                car_id=car_id,
                ip_address=client_ip,
                port=client_port,
                service_type=service_type,
                metadata=payload.get('metadata', {}),
                status=RequestStatus.CHECKING_AUTHENTICITY
            )
            logging.info(f"new Request has been created for car with client ip:{request.ip_address}. status:{request.status}")

            # Authenticate and process request
            if self.check_authentication(request):
                logging.info(f"Authentication success for request from client ip:{request.ip_address}")
                client_socket.send(Protocol.create_message(Protocol.HANDSHAKE, {
                    'status': 'authenticated',
                    'message': 'Connection established'
                }))

                # Initial update check
                logging.info(f"Performing initial update check for car ID: {car_id}")
                self.check_for_updates(request, client_socket)

                # Keep connection alive and handle subsequent requests
                logging.info(f"Maintaining connection for car ID: {car_id} to handle subsequent requests")
                while True:
                    logging.info(f"Waiting for next request from car ID: {car_id}")
                    message = self.receive_message(client_socket)
                    
                    if not message:
                        logging.info(f"Client {car_id} disconnected gracefully")
                        break

                    logging.info(f"Received request from car ID: {car_id}, message type: {message['type']}")

                    if message['type'] == Protocol.DOWNLOAD_REQUEST:
                        logging.info(f"Processing download request from car ID: {car_id}")
                        request.service_type = ServiceType.DOWNLOAD_UPDATE
                        request.metadata = message['payload']
                        self.handle_download_request(request, client_socket)
                        logging.info(f"Completed download request processing for car ID: {car_id}")
                    
                    elif message['type'] == Protocol.UPDATE_CHECK:
                        logging.info(f"Processing update check request from car ID: {car_id}")
                        request.service_type = ServiceType.CHECK_FOR_UPDATE
                        request.metadata = message['payload']
                        self.check_for_updates(request, client_socket)
                        logging.info(f"Completed update check for car ID: {car_id}")
                    
                    else:
                        logging.warning(f"Unknown message type '{message['type']}' received from car ID: {car_id}")
                        client_socket.send(Protocol.create_error_message(
                            400, f"Unknown message type: {message['type']}"
                        ))

            else:
                logging.info(f"Authentication failed for request from client ip:{request.ip_address}")
                client_socket.send(Protocol.create_error_message(401, "Authentication failed"))

        except socket.timeout:
            logging.error(f"Connection timeout for {client_ip}:{client_port}")
        except ConnectionError as e:
            logging.error(f"Connection error for {client_ip}:{client_port}: {str(e)}")
        except Exception as e:
            logging.error(f"Error handling client {client_ip}:{client_port}: {str(e)}")
        finally:
            try:
                logging.info(f"Closing connection for client {client_ip}:{client_port}")
                client_socket.close()
            except Exception as e:
                logging.error(f"Error closing connection for {client_ip}:{client_port}: {str(e)}")
            logging.info(f"Connection terminated for client {client_ip}:{client_port}")

    def check_authentication(self, request: Request) -> bool:
        """Authenticate the car request"""
        try:
            car_type = next((ct for ct in self.car_types 
                           if ct.name == request.car_type), None)
            
            if not car_type:
                request.status = RequestStatus.NON_AUTHENTICATED
                return False

            if request.car_id not in car_type.car_ids:
                request.status = RequestStatus.NON_AUTHENTICATED
                return False

            request.status = RequestStatus.AUTHENTICATED
            self.active_requests[request.car_id] = request
            return True

        except Exception as e:
            logging.error(f"Authentication error: {str(e)}")
            request.status = RequestStatus.FAILED
            return False
        
    def allocate_service(self, request: Request, client_socket: socket.socket):
        logging.info(f"allocating new service with service name:{request.service_type}")
        """Allocate appropriate service based on request type"""
        try:
            request.status = RequestStatus.SERVICE_IN_PROGRESS
            
            if request.service_type == ServiceType.CHECK_FOR_UPDATE:
                self.check_for_updates(request, client_socket)
            elif request.service_type == ServiceType.DOWNLOAD_UPDATE:
                self.handle_download_request(request, client_socket)
            else:
                logging.error(f"Unknown service type")
                raise Exception("Unknown service type")

        except Exception as e:
            logging.error(f"Service allocation error: {str(e)}")
            request.status = RequestStatus.FAILED
            client_socket.send(Protocol.create_error_message(
                500, "Service allocation failed"
            ))

    def check_for_updates(self, request: Request, client_socket: socket.socket):
        logging.info(f"checking-for-update method started processing for client:{request.ip_address}")
        """Check if updates are available for the car"""
        try:
            car_type = next((ct for ct in self.car_types 
                        if ct.name == request.car_type), None)
            
            if not car_type:
                raise Exception("Car type not found")

            # Get current versions from metadata
            current_versions = request.metadata.get('ecu_versions', {})
            
            # Check for updates
            updates_needed = car_type.check_for_updates(current_versions)
            logging.info(f"updates needed response for client with ip:{request.ip_address}")
            # Send response
            response = Protocol.create_update_response(updates_needed)
            
            client_socket.send(response)
            logging.info(f"updates needed response for client with ip:{request.ip_address} is send successfully with message:{response}")
            logging.info(f"Request for: {request.ip_address} finished successfully")
            request.status = RequestStatus.FINISHED_SUCCESSFULLY

        except Exception as e:
            logging.error(f"Update check error: {str(e)}")
            request.status = RequestStatus.FAILED
            client_socket.send(Protocol.create_error_message(
                500, "Update check failed"
            ))
            
    def handle_download_request(self, request: Request, client_socket: socket.socket):
        """Handle download request for new ECU versions"""
        try:
            # Get download information from metadata
            required_versions = request.metadata.get('required_versions', {})
            old_versions = request.metadata.get('old_versions', {})

            if not required_versions:
                raise Exception("No versions specified for download")

            # Create download request
            download_request = DownloadRequest(
                timestamp=datetime.now(),
                car_type=request.car_type,
                car_id=request.car_id,
                ip_address=request.ip_address,
                port=request.port,
                required_versions=required_versions,
                old_versions=old_versions,
                status=DownloadStatus.PREPARING_FILES,
                active_transfers={}
            )

            self.active_downloads[request.car_id] = download_request
            
            # Start download process
            self.send_new_versions(download_request, client_socket)

        except Exception as e:
            logging.error(f"Download request error: {str(e)}")
            request.status = RequestStatus.FAILED
            client_socket.send(Protocol.create_error_message(
                500, "Download request failed"
            ))

    def send_new_versions(self, download_request: DownloadRequest, client_socket: socket.socket):
        """Send new ECU versions to client"""
        try:
            car_type = next((ct for ct in self.car_types 
                           if ct.name == download_request.car_type), None)
            
            if not car_type:
                raise Exception("Car type not found")

            download_request.status = DownloadStatus.SENDING_IN_PROGRESS
            
            # Calculate total size and prepare file information
            files_info = {}
            total_size = 0
            
            for ecu_name, version_number in download_request.required_versions.items():
                ecu = next((e for e in car_type.ecus if e.name == ecu_name), None)
                if not ecu:
                    continue
                
                version = next((v for v in ecu.versions 
                              if v.version_number == version_number), None)
                if not version:
                    continue

                file_size = self.db_manager.get_file_size(version.hex_file_path)
                total_size += file_size
                files_info[ecu_name] = {
                    'path': version.hex_file_path,
                    'size': file_size,
                    'transferred': 0
                }

            download_request.total_size = total_size

            # Send download start message
            start_message = Protocol.create_message(Protocol.DOWNLOAD_START, {
                'total_size': total_size,
                'files': {name: info['size'] for name, info in files_info.items()}
            })
            client_socket.send(start_message)

            # Wait for client acknowledgment
            ack = self.receive_message(client_socket)
            if not ack or ack['type'] != "DOWNLOAD_ACK":
                raise Exception("Client did not acknowledge download start")

            # Send files
            successful_transfers = 0
            for ecu_name, file_info in files_info.items():
                try:
                    self.transfer_file(
                        client_socket,
                        ecu_name,
                        file_info['path'],
                        file_info['size'],
                        download_request
                    )
                    successful_transfers += 1
                except Exception as e:
                    logging.error(f"Error transferring {ecu_name}: {str(e)}")

            # Update final status
            if successful_transfers == len(files_info):
                download_request.status = DownloadStatus.FINISHED_SUCCESSFULLY
            elif successful_transfers > 0:
                download_request.status = DownloadStatus.FAILED_PARTIAL_SUCCESS
            else:
                download_request.status = DownloadStatus.ALL_FAILED

            # Send completion message
            completion_message = Protocol.create_message(Protocol.DOWNLOAD_COMPLETE, {
                'status': download_request.status.value,
                'successful_transfers': successful_transfers,
                'total_files': len(files_info)
            })
            client_socket.send(completion_message)

        except Exception as e:
            logging.error(f"File transfer error: {str(e)}")
            download_request.status = DownloadStatus.ALL_FAILED
            client_socket.send(Protocol.create_error_message(
                500, "File transfer failed"
            ))

    def transfer_file(self, client_socket: socket.socket, ecu_name: str, 
                     file_path: str, file_size: int, download_request: DownloadRequest):
        """Transfer a single file to client"""
        print(f"file_path: {file_path}")
        offset = 0
        while offset < file_size:
            chunk = self.db_manager.get_hex_file_chunk(file_path, self.chunk_size, offset)
            if not chunk:
                raise Exception(f"Failed to read chunk from {file_path}")

            # Create chunk message
            chunk_message = Protocol.create_message(Protocol.FILE_CHUNK, {
                'ecu_name': ecu_name,
                'offset': offset,
                'data': chunk.hex()  # Convert binary to hex string
            })
            client_socket.send(chunk_message)

            # Wait for chunk acknowledgment
            ack = self.receive_message(client_socket)
            if not ack or ack['type'] != "CHUNK_ACK":
                raise Exception("Chunk not acknowledged")

            offset += len(chunk)
            download_request.transferred_size += len(chunk)

    def receive_message(self, client_socket: socket.socket) -> Optional[Dict]:
        """Receive and parse a message from the client"""
        try:
            # First receive message length (10 bytes)
            length_data = b""
            while len(length_data) < 10:
                chunk = client_socket.recv(10 - len(length_data))
                if not chunk:
                    logging.error("Connection closed by peer while receiving message length")
                    return None
                length_data += chunk
            
            message_length = int(length_data.decode())
            
            # Receive the actual message
            message_data = b""
            while len(message_data) < message_length:
                remaining = message_length - len(message_data)
                chunk = client_socket.recv(min(self.chunk_size, remaining))
                if not chunk:
                    logging.error("Connection closed by peer while receiving message data")
                    return None
                message_data += chunk

            return Protocol.parse_message(message_data)

        except socket.timeout:
            logging.error("Socket timeout while receiving message")
            return None
        except ConnectionError as e:
            logging.error(f"Connection error while receiving message: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error receiving message: {str(e)}")
            return None

    def shutdown(self):
        """Shutdown the server"""
        self.running = False
        if self.socket:
            self.socket.close()