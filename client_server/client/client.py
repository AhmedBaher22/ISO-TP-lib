import socket
import threading
import time
import uuid
from datetime import datetime
from typing import Optional, Dict
import logging
from enums import *
from protocol import Protocol
from client_models import ClientDownloadRequest
from client_database import ClientDatabase
from shared_models import CarInfo

logging.basicConfig(level=logging.INFO)

class ECUUpdateClient:
    def __init__(self, server_host: str, server_port: int, data_directory: str):
        self.server_host = server_host
        self.server_port = server_port
        self.db = ClientDatabase(data_directory)
        self.car_info: Optional[CarInfo] = None
        self.status = ClientStatus.OFFLINE
        self.current_download: Optional[ClientDownloadRequest] = None
        self.socket: Optional[socket.socket] = None
        self.last_login: Optional[datetime] = None
        self.connection_timeout = 30  # seconds
        self.retry_limit = 3
        self.retry_delay = 5  # seconds
        self.running = False
        self.update_check_interval = 3600  # 1 hour
        self.chunk_size = 8192  # 8KB chunks for file transfer

    def start(self):
        """Start the client"""
        try:
            # Load car information
            self.car_info = self.db.load_car_info()
            if not self.car_info:
                raise Exception("Car information not found")

            # Check for incomplete downloads
            pending_download = self.db.load_download_request()
            if pending_download and pending_download.status not in [
                ClientDownloadStatus.COMPLETED, 
                ClientDownloadStatus.FAILED
            ]:
                self.current_download = pending_download

            self.running = True
            self.status = ClientStatus.OFFLINE

            # Start main client thread
            client_thread = threading.Thread(target=self.run)
            client_thread.daemon = True
            client_thread.start()

            logging.info("Client started successfully")

        except Exception as e:
            logging.error(f"Failed to start client: {str(e)}")
            self.shutdown()

    def run(self):
        """Main client loop"""
        while self.running:
            try:
                if self.status == ClientStatus.OFFLINE:
                    self.connect_to_server()
                
                elif self.status == ClientStatus.VERSIONS_UP_TO_DATE:
                    # Periodically check for updates
                    time.sleep(self.update_check_interval)
                    self.check_for_updates()
                
                elif self.status == ClientStatus.DOWNLOAD_NEEDED:
                    self.initiate_download()
                
                time.sleep(1)  # Prevent CPU overuse

            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                self.status = ClientStatus.OFFLINE
                time.sleep(self.retry_delay)

    def connect_to_server(self):
        """Connect to update server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.connection_timeout)
            self.socket.connect((self.server_host, self.server_port))

            # Send handshake
            handshake_message = Protocol.create_message(Protocol.HANDSHAKE, {
                'car_type': self.car_info.car_type,
                'car_id': self.car_info.car_id,
                'service_type': ServiceType.CHECK_FOR_UPDATE.value,
                'metadata': {
                    'ecu_versions': self.car_info.ecu_versions
                }
            })
            self.socket.send(handshake_message)

            # Process handshake response
            response = self.receive_message()
            if not response:
                raise Exception("No response from server")

            if response['type'] == Protocol.ERROR:
                raise Exception(f"Server error: {response['payload']['message']}")

            self.last_login = datetime.now()
            self.status = ClientStatus.CHECK_FOR_UPDATES
            self.check_for_updates()

        except socket.timeout:
            logging.error("Connection timeout")
            self.status = ClientStatus.CONNECTION_TIMEOUT
            self.cleanup_connection()
        except Exception as e:
            logging.error(f"Connection error: {str(e)}")
            self.status = ClientStatus.OFFLINE
            self.cleanup_connection()

    def check_for_updates(self):
        """Check for available updates"""
        try:
            if not self.socket:
                self.connect_to_server()
                return

            self.status = ClientStatus.CHECK_FOR_UPDATES
            
            # Send update check request
            check_message = Protocol.create_message(Protocol.UPDATE_CHECK, {
                'car_type': self.car_info.car_type,
                'car_id': self.car_info.car_id,
                'ecu_versions': self.car_info.ecu_versions
            })
            self.socket.send(check_message)

            # Wait for response
            self.status = ClientStatus.WAITING_FOR_RESPONSE
            response = self.receive_message()

            if not response:
                raise Exception("No response from server")

            if response['type'] == Protocol.UPDATE_RESPONSE:
                updates_needed = response['payload']['updates_needed']
                if updates_needed:
                    self.status = ClientStatus.DOWNLOAD_NEEDED
                    self.prepare_download_request(updates_needed)
                else:
                    self.status = ClientStatus.VERSIONS_UP_TO_DATE
            else:
                raise Exception("Invalid response type")

        except Exception as e:
            logging.error(f"Update check error: {str(e)}")
            self.status = ClientStatus.OFFLINE
            self.cleanup_connection()
    def prepare_download_request(self, updates_needed: Dict[str, str]):
        """Prepare download request for new ECU versions"""
        try:
            self.current_download = ClientDownloadRequest(
                request_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                car_info=self.car_info,
                required_updates=updates_needed,
                status=ClientDownloadStatus.INITIALIZING,
                total_ecus=len(updates_needed),
                completed_ecus=0
            )
            
            # Save initial download request
            self.db.save_download_request(self.current_download)
            
            # Start download in new thread
            download_thread = threading.Thread(target=self.download_updates)
            download_thread.daemon = True
            download_thread.start()

        except Exception as e:
            logging.error(f"Error preparing download: {str(e)}")
            self.status = ClientStatus.OFFLINE

    def download_updates(self):
        """Handle the download of new ECU versions"""
        try:
            if not self.current_download:
                raise Exception("No download request available")

            self.current_download.status = ClientDownloadStatus.REQUESTING
            self.status = ClientStatus.REQUESTING_DOWNLOAD

            # Send download request
            download_message = Protocol.create_message(Protocol.DOWNLOAD_REQUEST, {
                'request_id': self.current_download.request_id,
                'car_type': self.car_info.car_type,
                'car_id': self.car_info.car_id,
                'required_versions': self.current_download.required_updates,
                'old_versions': self.car_info.ecu_versions
            })
            self.socket.send(download_message)

            # Wait for download start response
            response = self.receive_message()
            if not response or response['type'] != Protocol.DOWNLOAD_START:
                raise Exception("Invalid download start response")

            # Update download information
            download_info = response['payload']
            self.current_download.total_size = download_info['total_size']
            self.status = ClientStatus.DOWNLOAD_IN_PROGRESS
            self.current_download.status = ClientDownloadStatus.DOWNLOADING

            # Send acknowledgment
            self.socket.send(Protocol.create_message("DOWNLOAD_ACK", {'status': 'ready'}))

            # Start receiving files
            self.receive_files()

        except Exception as e:
            logging.error(f"Download error: {str(e)}")
            self.current_download.status = ClientDownloadStatus.FAILED
            self.status = ClientStatus.OFFLINE
            self.db.save_download_request(self.current_download)
            self.cleanup_connection()

    def receive_files(self):
        """Receive ECU update files from server"""
        try:
            while True:
                message = self.receive_message()
                if not message:
                    raise Exception("Connection lost during file transfer")

                if message['type'] == Protocol.FILE_CHUNK:
                    self.handle_file_chunk(message['payload'])
                elif message['type'] == Protocol.DOWNLOAD_COMPLETE:
                    self.handle_download_completion(message['payload'])
                    break
                elif message['type'] == Protocol.ERROR:
                    raise Exception(f"Server error: {message['payload']['message']}")

        except Exception as e:
            logging.error(f"File reception error: {str(e)}")
            self.current_download.status = ClientDownloadStatus.FAILED
            self.db.save_download_request(self.current_download)

    def handle_file_chunk(self, payload: Dict):
        """Handle received file chunk"""
        try:
            ecu_name = payload['ecu_name']
            offset = payload['offset']
            data = bytes.fromhex(payload['data'])

            # Save chunk to temporary file
            temp_path = f"temp_{ecu_name}_{self.current_download.request_id}.hex"
            with open(temp_path, 'ab') as f:
                f.seek(offset)
                f.write(data)

            # Update progress
            self.current_download.downloaded_size += len(data)
            
            # Send chunk acknowledgment
            self.socket.send(Protocol.create_message("CHUNK_ACK", {
                'ecu_name': ecu_name,
                'offset': offset,
                'status': 'received'
            }))

            # Save progress
            self.db.save_download_request(self.current_download)

        except Exception as e:
            logging.error(f"Chunk handling error: {str(e)}")
            raise

    def handle_download_completion(self, payload: Dict):
        """Handle download completion"""
        try:
            if payload['status'] == DownloadStatus.FINISHED_SUCCESSFULLY.value:
                # Move temporary files to final location
                for ecu_name, version in self.current_download.required_updates.items():
                    temp_path = f"temp_{ecu_name}_{self.current_download.request_id}.hex"
                    if os.path.exists(temp_path):
                        with open(temp_path, 'rb') as f:
                            hex_data = f.read()
                        
                        # Save to final location
                        final_path = self.db.save_ecu_version(ecu_name, version, hex_data)
                        self.current_download.downloaded_versions[ecu_name] = version
                        self.current_download.completed_ecus += 1
                        
                        # Clean up temp file
                        os.remove(temp_path)

                self.current_download.status = ClientDownloadStatus.COMPLETED
                self.flash_updates()
            else:
                self.current_download.status = ClientDownloadStatus.FAILED

            self.db.save_download_request(self.current_download)

        except Exception as e:
            logging.error(f"Download completion error: {str(e)}")
            self.current_download.status = ClientDownloadStatus.FAILED
            self.db.save_download_request(self.current_download)

    def flash_updates(self):
        """Flash downloaded ECU updates"""
        try:
            # This is a placeholder for the actual flashing implementation
            logging.info("Starting ECU flashing process...")
            
            for ecu_name, version in self.current_download.downloaded_versions.items():
                logging.info(f"Would flash ECU {ecu_name} with version {version}")
                # Update car info with new version
                self.car_info.ecu_versions[ecu_name] = version

            # Save updated car info
            self.db.save_car_info(self.car_info)
            
            logging.info("ECU flashing process completed")
            self.status = ClientStatus.VERSIONS_UP_TO_DATE

        except Exception as e:
            logging.error(f"Flashing error: {str(e)}")
            self.status = ClientStatus.OFFLINE

    def receive_message(self) -> Optional[Dict]:
        """Receive and parse a message from the server"""
        try:
            # First receive message length (10 bytes)
            length_data = self.socket.recv(10)
            if not length_data:
                return None
            
            message_length = int(length_data.decode())
            
            # Receive the actual message
            message_data = b""
            while len(message_data) < message_length:
                chunk = self.socket.recv(min(self.chunk_size, message_length - len(message_data)))
                if not chunk:
                    return None
                message_data += chunk

            return Protocol.parse_message(message_data)

        except Exception as e:
            logging.error(f"Error receiving message: {str(e)}")
            return None

    def cleanup_connection(self):
        """Clean up socket connection"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

    def shutdown(self):
        """Shutdown the client"""
        self.running = False
        self.cleanup_connection()