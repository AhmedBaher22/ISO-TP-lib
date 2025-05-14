"""
ECU Update Client with State Design Pattern
-------------------------------------------
This client manages ECU updates using a state pattern to ensure
operations only occur when explicitly requested by the user.
"""

import socket
import threading
import time
import uuid
import os
import logging
import sys
from datetime import datetime
from typing import Optional, Dict

current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
# Import backend modules 
from client_server.client.enums import ClientStatus, ClientDownloadStatus, ServiceType, DownloadStatus
from client_server.client.protocol import Protocol
from client_server.client.client_models import ClientDownloadRequest, flashingEcu
from client_server.client.client_database import ClientDatabase
from client_server.client.shared_models import CarInfo
from delta_generator.DeltaGenerator import DeltaGenerator, DeltaAlgorithm
from hex_parser.SRecordParser import SRecordParser
from app_initialization import init_uds_client

# Base State Class
class ClientState:
    """Base state class for the client state pattern"""
    def __init__(self, client):
        self.client = client
    
    def connect_to_server(self) -> bool:
        """Connect to update server - to be implemented by concrete states"""
        return False
    
    def check_for_updates(self) -> bool:
        """Check for available updates - to be implemented by concrete states"""
        return False
    
    def initiate_download(self) -> bool:
        """Initiate download of updates - to be implemented by concrete states"""
        return False
    
    def download_updates(self) -> bool:
        """Download updates - to be implemented by concrete states"""
        return False
    
    def flash_updates(self) -> bool:
        """Flash downloaded ECU updates - to be implemented by concrete states"""
        return False
    
    def resume_download(self) -> bool:
        """Resume interrupted download - to be implemented by concrete states"""
        return False
    
    def resume_flashing(self) -> bool:
        """Resume interrupted flashing - to be implemented by concrete states"""
        return False
    
    def cancel_operation(self) -> bool:
        """Cancel current operation - to be implemented by concrete states"""
        return False


class OfflineState(ClientState):
    """State when client is disconnected from server"""
    def connect_to_server(self) -> bool:
        """Connect to update server"""
        retry_count = 0
        while retry_count < self.client.retry_limit and self.client.running:
            try:
                if self.client.socket:
                    self.client.cleanup_connection()

                self.client.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.socket.settimeout(self.client.connection_timeout)
                self.client.socket.connect((self.client.server_host, self.client.server_port))

                # Send handshake
                handshake_message = Protocol.create_message(Protocol.HANDSHAKE, {
                    'car_type': self.client.car_info.car_type,
                    'car_id': self.client.car_info.car_id,
                    'service_type': ServiceType.CHECK_FOR_UPDATE.value,
                    'metadata': {
                        'ecu_versions': self.client.car_info.ecu_versions
                    }
                })
                logging.info(f"Handshake message created and ready to be sent: {handshake_message}")
                self.client.socket.send(handshake_message)

                # Process handshake response
                response = self.client.receive_message()
                if not response:
                    raise Exception("No response from server")

                if response['type'] == Protocol.ERROR:
                    raise Exception(f"Server error: {response['payload']['message']}")

                logging.info(f"Successfully logged in to the server: {str(response)}")
                self.client.last_login = datetime.now()
                
                # Change state to authenticated
                self.client.state = AuthenticatedState(self.client)
                self.client.status = ClientStatus.AUTHENTICATED
                
                # Receive update check response from server (server automatically sends this)
                update_response = self.client.receive_message()
                
                if not update_response:
                    raise Exception("No update check response from server")

                if update_response['type'] == Protocol.UPDATE_RESPONSE:
                    updates_needed = update_response['payload']['updates_needed']
                    if updates_needed:
                        logging.info(f"Updates available: {updates_needed}")
                        self.client.status = ClientStatus.DOWNLOAD_NEEDED
                        self.client.prepare_download_request(updates_needed)
                    else:
                        logging.info("System is up to date")
                        self.client.status = ClientStatus.VERSIONS_UP_TO_DATE
                else:
                    raise Exception("Invalid update check response type")

                return True
                
            except socket.timeout:
                logging.error(f"Connection attempt {retry_count + 1} timed out")
            except ConnectionRefusedError:
                logging.error(f"Connection attempt {retry_count + 1} refused - Is the server running?")
            except Exception as e:
                logging.error(f"Connection attempt {retry_count + 1} failed: {str(e)}")

            retry_count += 1
            if retry_count < self.client.retry_limit:
                time.sleep(self.client.retry_delay)

        self.client.status = ClientStatus.OFFLINE
        return False


class AuthenticatedState(ClientState):
    """State when client is authenticated with server"""
    def check_for_updates(self) -> bool:
        """Check for available updates"""
        try:
            if not self.client.socket:
                return self.client.state.connect_to_server()

            self.client.status = ClientStatus.CHECK_FOR_UPDATES
            
            # Send update check request
            check_message = Protocol.create_message(Protocol.UPDATE_CHECK, {
                'car_type': self.client.car_info.car_type,
                'car_id': self.client.car_info.car_id,
                'ecu_versions': self.client.car_info.ecu_versions
            })
            logging.info(f"Checking for updates: {check_message}")            
            self.client.socket.send(check_message)

            # Wait for response
            self.client.status = ClientStatus.WAITING_FOR_RESPONSE 
            response = self.client.receive_message()

            if not response:    
                raise Exception("No response from server")

            logging.info(f"Server response: {response['payload']['message']}")

            if response['type'] == Protocol.UPDATE_RESPONSE:
                updates_needed = response['payload']['updates_needed']
                if updates_needed:
                    logging.info("Updates needed")
                    self.client.status = ClientStatus.DOWNLOAD_NEEDED
                    self.client.prepare_download_request(updates_needed)
                    return True
                else:
                    logging.info("All car versions up to date")
                    self.client.status = ClientStatus.VERSIONS_UP_TO_DATE
                    return False
            else:
                raise Exception("Invalid response type")

        except Exception as e:
            logging.error(f"Update check error: {str(e)}")
            self.client.status = ClientStatus.OFFLINE
            self.client.state = OfflineState(self.client)
            self.client.cleanup_connection()
            return False


class DownloadNeededState(ClientState):
    """State when updates are available and need to be downloaded"""
    def initiate_download(self) -> bool:
        """Initiate download process"""
        # Check if we have a valid download request
        if not self.client.current_download:
            logging.error("No download request available")
            return False
        
        # Set appropriate status and state
        self.client.status = ClientStatus.REQUESTING_DOWNLOAD
        self.client.current_download.status = ClientDownloadStatus.REQUESTING
        
        try:
            # Start download in new thread to avoid blocking the UI
            download_thread = threading.Thread(target=self.download_updates)
            download_thread.daemon = True
            download_thread.start()
            return True
        except Exception as e:
            logging.error(f"Failed to start download thread: {str(e)}")
            return False
    
    def download_updates(self) -> bool:
        """Download ECU updates"""
        try:
            if not self.client.current_download:
                raise Exception("No download request available")

            # Check if this is a resume
            file_offsets = self.client.current_download.file_offsets or {}
            is_resume = bool(file_offsets)
            
            if len(file_offsets) > 0:
                logging.info(f"Resuming download. Progress: {self.client.current_download.file_offsets}")
            
            # Send download request with resume information
            download_message = Protocol.create_message(Protocol.DOWNLOAD_REQUEST, {
                'request_id': self.client.current_download.request_id,
                'car_type': self.client.car_info.car_type,
                'car_id': self.client.car_info.car_id,
                'required_versions': self.client.current_download.required_updates,
                'old_versions': self.client.car_info.ecu_versions,
                'file_offsets': file_offsets
            })
            
            self.client.socket.send(download_message)
            logging.info(f"Download request sent: {download_message}")

            # Wait for download start response
            response = self.client.receive_message()
            if not response or response['type'] != Protocol.DOWNLOAD_START:
                raise Exception("Invalid download start response")

            logging.info(f"Received download metadata: {response}")
            
            # Update download information
            download_info = response['payload']
            if not is_resume:
                self.client.current_download.total_size = download_info['total_size']
            
            self.client.status = ClientStatus.DOWNLOAD_IN_PROGRESS
            self.client.current_download.status = ClientDownloadStatus.DOWNLOADING

            # Send acknowledgment
            self.client.socket.send(Protocol.create_message("DOWNLOAD_ACK", {'status': 'ready'}))
            logging.info("Download acknowledgment sent")

            # Start receiving files
            self.client.receive_files()
            return True

        except Exception as e:
            logging.error(f"Download error: {str(e)}")
            self.client.current_download.status = ClientDownloadStatus.FAILED
            self.client.status = ClientStatus.OFFLINE
            self.client.state = OfflineState(self.client)
            self.client.db.save_download_request(self.client.current_download)
            self.client.cleanup_connection()
            return False
    
    def resume_download(self) -> bool:
        """Resume an interrupted download"""
        # This is handled by initiate_download, since it checks file offsets
        return self.initiate_download()


class DownloadCompleteState(ClientState):
    """State when downloads are complete and ready for flashing"""
    def flash_updates(self) -> bool:
        """Flash downloaded ECU updates"""
        try:
            # This is a placeholder for the actual flashing implementation
            logging.info("Starting ECU flashing process...")
            
            # Move to flashing state
            self.client.current_download.status = ClientDownloadStatus.IN_FLASHING
            self.client.status = ClientStatus.WAITING_FLASHING_SOME_ECUS
            
            n = 0
            for ecu_name, version in self.client.current_download.downloaded_versions.items():
                logging.info(f"Preparing to flash ECU {ecu_name} with version {version}")

                old_version = self.client.car_info.ecu_versions[ecu_name]
                new_version = version
                
                # Generate delta and rollback delta
                deltaGenerator = DeltaGenerator(algorithm=DeltaAlgorithm.SENDING_COMPLETE_SECTOR)
                old_version_path = self.client.db.get_ecu_version_path(ecu_name=ecu_name, version=old_version)
                new_version_path = self.client.db.get_ecu_version_path(ecu_name=ecu_name, version=new_version)
                
                parser = SRecordParser()
                parser2 = SRecordParser()
                parser.parse_file(filename=str(old_version_path))
                old_version_data_records = parser._merged_records
                parser2.parse_file(filename=str(new_version_path))
                new_version_data_records = parser2._merged_records
                
                delta_records = deltaGenerator.generate_delta(old_version=old_version_data_records, new_version=new_version_data_records)
                roll_back_delta = deltaGenerator.generate_delta(old_version=new_version_data_records, new_version=old_version_data_records)

                new_flash_request = flashingEcu(
                    ecu_number=n,
                    old_version_path=old_version_path,
                    new_version_path=new_version_path,
                    delta_records=delta_records,
                    flashing_done=False,
                    ecu_name=ecu_name,
                    old_version=old_version,
                    new_version=new_version,
                    roll_back_delta=roll_back_delta,
                    old_version_data_records=old_version_data_records
                )

                self.client.current_download.flashed_ecus.append(new_flash_request)
                n += 1   

            logging.info("Flash ECU objects prepared")
            self.client.db.save_download_request(self.client.current_download)
            
            # Start the actual flashing process
            flash_thread = threading.Thread(target=self.client.UDS_flash)
            flash_thread.daemon = True
            flash_thread.start()
            return True
            
        except Exception as e:
            logging.error(f"Flashing preparation error: {str(e)}")
            self.client.status = ClientStatus.OFFLINE
            self.client.state = OfflineState(self.client)
            return False
    
    def resume_flashing(self) -> bool:
        """Resume interrupted flashing"""
        if not self.client.current_download or self.client.current_download.status != ClientDownloadStatus.IN_FLASHING:
            logging.error("No flashing operation to resume")
            return False
        
        try:
            self.client.status = ClientStatus.WAITING_FLASHING_SOME_ECUS
            
            # Start the flashing process in a separate thread
            flash_thread = threading.Thread(target=self.client.UDS_flash)
            flash_thread.daemon = True
            flash_thread.start()
            return True
            
        except Exception as e:
            logging.error(f"Error resuming flashing: {str(e)}")
            return False


class ECUUpdateClient:
    """Client for ECU updates with explicit user actions"""
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
        self.uds_client = None
        
        # Initialize to the offline state
        self.state = OfflineState(self)
        
        # Setup necessary directories
        os.makedirs(data_directory, exist_ok=True)

    def start(self):
        """Start the client"""
        try:
            # Load car information
            self.car_info = self.db.load_car_info()
            if not self.car_info:
                raise Exception("Car information not found")
            
            logging.info(f"Car information loaded: {self.car_info}")
            logging.info("Checking for pending download requests")
            
            # Check for incomplete downloads
            pending_download = self.db.load_download_request()
            
            if pending_download and pending_download.status not in [
                ClientDownloadStatus.COMPLETED, 
                ClientDownloadStatus.FAILED
            ]:
                self.current_download = pending_download
                logging.info(f"Pending download request found: {pending_download.status}")
                
                # Set appropriate state based on download status
                if pending_download.status == ClientDownloadStatus.DOWNLOADING:
                    self.state = DownloadNeededState(self)
                    self.status = ClientStatus.DOWNLOAD_NEEDED
                elif pending_download.status == ClientDownloadStatus.IN_FLASHING:
                    self.state = DownloadCompleteState(self)
                    self.status = ClientStatus.WAITING_FLASHING_SOME_ECUS
            else:
                logging.info("No pending download request found")

            self.running = True
            
            # Start initial connection
            connection_thread = threading.Thread(target=self.connect_to_server)
            connection_thread.daemon = True
            connection_thread.start()

            logging.info("Client started successfully")

        except Exception as e:
            logging.error(f"Failed to start client: {str(e)}")
            self.shutdown()
    
    def connect_to_server(self):
        """Connect to the update server"""
        self.state.connect_to_server()
    
    def check_for_updates(self):
        """Check for available updates"""
        return self.state.check_for_updates()
    
    def prepare_download_request(self, updates_needed: Dict[str, str]):
        """Prepare download request for new ECU versions"""
        try:
            # Check if there's an existing download request
            if self.current_download and self.current_download.status == ClientDownloadStatus.DOWNLOADING:
                logging.info("Found failed download request, attempting to resume")
                self.verify_temp_files()
            else:
                self.current_download = ClientDownloadRequest(
                    request_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    car_info=self.car_info,
                    required_updates=updates_needed,
                    status=ClientDownloadStatus.INITIALIZING,
                    total_ecus=len(updates_needed),
                    completed_ecus=0,
                    downloaded_versions={},
                    file_offsets={}
                )
            
            logging.info(f"Download request prepared: {self.current_download.status}")
            
            # Save initial download request
            self.db.save_download_request(self.current_download)
            
            # Update client state
            self.state = DownloadNeededState(self)
            
        except Exception as e:
            logging.error(f"Error preparing download: {str(e)}")
            self.status = ClientStatus.OFFLINE
            self.state = OfflineState(self)
    
    def verify_temp_files(self):
        """Verify temporary files and their sizes"""
        try:
            for ecu_name in self.current_download.required_updates.keys():
                temp_path = f"temp_{ecu_name}_{self.current_download.request_id}.srec"
                if os.path.exists(temp_path):
                    size = os.path.getsize(temp_path)
                    self.current_download.file_offsets[ecu_name] = size
                    logging.info(f"Found existing temporary file for {ecu_name} with size {size} bytes")
                else:
                    self.current_download.file_offsets[ecu_name] = 0
                    logging.info(f"No existing temporary file found for {ecu_name}, will start from beginning")
        except Exception as e:
            logging.error(f"Error verifying temp files: {str(e)}")
    
    def initiate_download(self):
        """Initiate download of updates"""
        return self.state.initiate_download()
    
    def receive_files(self):
        """Receive ECU update files from server"""
        message_count = 1
        try:
            while True:
                self.current_download.status = ClientDownloadStatus.DOWNLOADING
                message = self.receive_message()
                message_count += 1
                
                if not message:
                    raise Exception("Connection lost during file transfer")

                if message['type'] == Protocol.FILE_CHUNK:
                    logging.info(f"Received file chunk #{message_count}")
                    self.handle_file_chunk(message['payload'])
                elif message['type'] == Protocol.DOWNLOAD_COMPLETE:
                    logging.info(f"Download complete message received")
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
            temp_path = f"temp_{ecu_name}_{self.current_download.request_id}.srec"
            with open(temp_path, 'ab') as f:
                f.seek(offset)
                f.write(data)

            # Update progress and offset
            self.current_download.downloaded_size = self.current_download.downloaded_size + len(data) if hasattr(self.current_download, 'downloaded_size') else len(data)
            self.current_download.file_offsets[ecu_name] = offset + len(data)
            
            # Log progress
            if hasattr(self.current_download, 'total_size') and self.current_download.total_size > 0:
                total_progress = (self.current_download.downloaded_size / self.current_download.total_size) * 100
                logging.info(f"Download progress for {ecu_name}: {total_progress:.2f}% (Offset: {offset + len(data)} bytes)")
            
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
                    temp_path = f"temp_{ecu_name}_{self.current_download.request_id}.srec"
                    if os.path.exists(temp_path):
                        with open(temp_path, 'rb') as f:
                            hex_data = f.read()
                        
                        # Save to final location
                        final_path = self.db.save_ecu_version(ecu_name, version, hex_data)
                        self.current_download.downloaded_versions[ecu_name] = version
                        self.current_download.completed_ecus += 1
                        
                        # Clean up temp file
                        os.remove(temp_path)


                self.current_download.status = ClientDownloadStatus.DOWNLOAD_COMPLETED
                self.status = ClientStatus.DOWNLOAD_COMPLETED
                
                # Update state to download complete
                self.state = DownloadCompleteState(self)
                
                self.db.save_download_request(self.current_download)
                logging.info("Download completed successfully, ready for flashing")
            else:
                self.current_download.status = ClientDownloadStatus.FAILED
                self.status = ClientStatus.OFFLINE
                self.state = OfflineState(self)

            self.db.save_download_request(self.current_download)

        except Exception as e:
            logging.error(f"Download completion error: {str(e)}")
            self.current_download.status = ClientDownloadStatus.FAILED
            self.status = ClientStatus.OFFLINE
            self.state = OfflineState(self)
            self.db.save_download_request(self.current_download)
    
    def flash_updates(self):
        """Flash downloaded ECU updates"""
        return self.state.flash_updates()
    
    def resume_download(self):
        """Resume interrupted download"""
        return self.state.resume_download()
    
    def resume_flashing(self):
        """Resume interrupted flashing"""
        return self.state.resume_flashing()
    
    def cancel_operation(self):
        """Cancel current operation"""
        if self.current_download:
            self.current_download.status = ClientDownloadStatus.FAILED
            self.db.save_download_request(self.current_download)
        
        self.status = ClientStatus.OFFLINE
        self.state = OfflineState(self)
        self.cleanup_connection()
        return True
    
    def UDS_flash(self):
        """Flash ECUs using UDS"""
        if self.current_download:
            if self.current_download.number_of_flashed_ecus == len(self.current_download.flashed_ecus):
                self.status = ClientStatus.VERSIONS_UP_TO_DATE
                raise Exception("Error: Trying to flash some updates but all current downloads are flashed successfully")
            else:
                if not self.uds_client:
                    self.uds_client = init_uds_client()
                if not self.uds_client:
                    raise Exception("Error: error initializing the uds layer")
                else:
                    logging.info("=== Initializing Communication with ECU ===")
                    # Here should be a function that retrieves the DA address of ecu from its name
                    from iso_tp_layer.Address import Address
                    from uds_layer.uds_enums import SessionType
                    
                    ecu_address = Address(addressing_mode=0, txid=0x55, rxid=0x55)
                    self.uds_client.add_server(ecu_address, SessionType.PROGRAMMING)
                    time.sleep(1)
                    
                    servers = self.uds_client.get_servers()
                    if not servers[self.current_download.flashed_order_index]:
                        logging.info(f"Error initializing Programming session with ECU to be updated, ecu name: {self.current_download.flashed_ecus[self.current_download.flashed_order_index].ecu_name}")
                        self.handle_failed_flashing(self.current_download.flashed_order_index, erasing_happen=False)
                        return
                    else:
                        self.status = ClientStatus.WAITING_FLASHING_SOME_ECUS
                        data_records = []
                        
                        if (self.current_download.flashed_ecus[self.current_download.flashed_order_index].roll_back_needed == True) and (self.current_download.flashed_ecus[self.current_download.flashed_order_index].roll_back_done == False) and (self.current_download.flashed_ecus[self.current_download.flashed_order_index].flashing_retries >= 4):
                            data_records = self.current_download.flashed_ecus[self.current_download.flashed_order_index].old_version_data_records
                            logging.info("Using old version data records for rollback")
                        elif (self.current_download.flashed_ecus[self.current_download.flashed_order_index].roll_back_needed == True) and (self.current_download.flashed_ecus[self.current_download.flashed_order_index].roll_back_done == False) and (self.current_download.flashed_ecus[self.current_download.flashed_order_index].flashing_retries >= 3):
                            data_records = self.current_download.flashed_ecus[self.current_download.flashed_order_index].roll_back_delta
                            logging.info("Using rollback delta records")
                        else:
                            data_records = self.current_download.flashed_ecus[self.current_download.flashed_order_index].delta_records
                            logging.info("Using normal delta records for update")
                            
                        logging.info(f"Started UDS flashing for ecu: {self.current_download.flashed_ecus[self.current_download.flashed_order_index].ecu_name}, with version: {self.current_download.flashed_ecus[self.current_download.flashed_order_index].new_version}")
                        
                        from uds_layer.transfer_enums import EncryptionMethod, CompressionMethod, CheckSumMethod
                        
                        self.uds_client.Flash_ECU(
                            segments=data_records,
                            recv_DA=servers[self.current_download.flashed_order_index].can_id,
                            encryption_method=EncryptionMethod.SEC_P_256_R1,
                            compression_method=CompressionMethod.LZ4,
                            checksum_required=CheckSumMethod.CRC_32,
                            on_successfull_flashing=self.handle_successful_flashing,
                            on_failing_flashing=self.handle_failed_flashing,
                            flashed_ecu_number=self.current_download.flashed_order_index
                        )
        else:
            raise Exception("Error: Trying to flash some updates but no current downloads found")
    
    def handle_successful_flashing(self, ecu_number: int):
        """Handle successful ECU flashing"""
        if self.current_download.flashed_ecus[ecu_number].roll_back_needed == True and self.current_download.flashed_ecus[ecu_number].flashing_retries > 3:
            self.current_download.flashed_ecus[ecu_number].roll_back_done = True
        else:    
            self.current_download.flashed_ecus[ecu_number].flashing_done = True

        self.current_download.flashed_order_index += 1
        self.current_download.number_of_flashed_ecus += 1

        logging.info(f"Successfully flashed ECU #{ecu_number}: {self.current_download.flashed_ecus[ecu_number].ecu_name}")
        
        if self.current_download.number_of_flashed_ecus >= len(self.current_download.flashed_ecus):
            check_all_up_to_date_flag = False
            rolled_back_ecus = []
            
            for n in self.current_download.flashed_ecus:
                if (n.roll_back_done == True) and (n.flashing_done == False):
                    rolled_back_ecus.append(n.ecu_name)
                    check_all_up_to_date_flag = True
                    
            if check_all_up_to_date_flag == True:
                self.status = ClientStatus.VERSIONS_UP_TO_DATE
                self.current_download.status = ClientDownloadStatus.FAILED
                
                version_updated = ""
                if (self.current_download.flashed_ecus[ecu_number].roll_back_needed == True) and (self.current_download.flashed_ecus[ecu_number].flashing_done == False):
                    version_updated = self.current_download.flashed_ecus[ecu_number].old_version
                    logging.info(f"ECU: {self.current_download.flashed_ecus[ecu_number].ecu_name} is rolled back successfully with version: {version_updated}")
                    self.car_info.ecu_versions[self.current_download.flashed_ecus[ecu_number].ecu_name] = self.current_download.flashed_ecus[ecu_number].old_version
                else:
                    version_updated = self.current_download.flashed_ecus[ecu_number].new_version
                    logging.info(f"ECU: {self.current_download.flashed_ecus[ecu_number].ecu_name} is updated successfully with version: {version_updated}")
                    self.car_info.ecu_versions[self.current_download.flashed_ecus[ecu_number].ecu_name] = self.current_download.flashed_ecus[ecu_number].new_version                    
            
                if len(rolled_back_ecus) > 0:
                    logging.info(f"Flashing process finished but not all ECUs updated and flashed. Some rolled back to old version: {rolled_back_ecus}, Try contacting with COMPANY CAR MAINTENANCE COMPANY.")
                else:
                    logging.info(f"Flashing process finished, all ECUs updated.")
                
            else:
                version_updated = self.current_download.flashed_ecus[ecu_number].new_version
                logging.info(f"ECU: {self.current_download.flashed_ecus[ecu_number].ecu_name} is updated successfully with version: {version_updated}")                       
                self.status = ClientStatus.VERSIONS_UP_TO_DATE
                self.current_download.status = ClientDownloadStatus.COMPLETED
                logging.info(f"ECU: {self.current_download.flashed_ecus[ecu_number].ecu_name} is updated successfully with version: {self.current_download.flashed_ecus[ecu_number].new_version}")
                logging.info("All ECUs updated and flashed successfully and all of them up to date now.")
                self.car_info.ecu_versions[self.current_download.flashed_ecus[ecu_number].ecu_name] = self.current_download.flashed_ecus[ecu_number].new_version
            
            self.db.save_car_info(self.car_info)
            self.db.save_download_request(self.current_download)
            return
            
        else:
            if (self.current_download.flashed_ecus[ecu_number].roll_back_needed == True) and (self.current_download.flashed_ecus[ecu_number].flashing_done == False):
                self.current_download.flashed_ecus[ecu_number].roll_back_done = True
                self.status = ClientStatus.WAITING_FLASHING_SOME_ECUS
                self.current_download.status = ClientDownloadStatus.IN_FLASHING
                logging.info(f"ECU: {self.current_download.flashed_ecus[ecu_number].ecu_name} is rolled back successfully with version: {self.current_download.flashed_ecus[ecu_number].old_version}")
                self.car_info.ecu_versions[self.current_download.flashed_ecus[ecu_number].ecu_name] = self.current_download.flashed_ecus[ecu_number].old_version
                self.db.save_car_info(self.car_info)
                self.db.save_download_request(self.current_download)
                logging.info("Preparing to flash the next ECU")
                self.UDS_flash()
            else: 
                self.status = ClientStatus.WAITING_FLASHING_SOME_ECUS
                self.current_download.status = ClientDownloadStatus.IN_FLASHING
                logging.info(f"ECU: {self.current_download.flashed_ecus[ecu_number].ecu_name} is updated successfully with version: {self.current_download.flashed_ecus[ecu_number].new_version}")
                self.car_info.ecu_versions[self.current_download.flashed_ecus[ecu_number].ecu_name] = self.current_download.flashed_ecus[ecu_number].new_version
                self.db.save_car_info(self.car_info)
                self.db.save_download_request(self.current_download)
                logging.info("Preparing to flash the next ECU")
                self.UDS_flash()
    
    def handle_failed_flashing(self, ecu_number: int, erasing_happen: bool):
        """Handle failed ECU flashing"""
        if erasing_happen == True:
            self.current_download.flashed_ecus[ecu_number].roll_back_needed = True
        
        self.current_download.flashed_ecus[ecu_number].flashing_retries += 1

        if self.current_download.flashed_ecus[ecu_number].flashing_retries >= 13 and self.current_download.flashed_ecus[ecu_number].roll_back_needed == True:
            logging.info(f"ECU: {self.current_download.flashed_ecus[ecu_number].ecu_name} failed to roll back to old version")
            logging.info(f"SAFETY ECU: {self.current_download.flashed_ecus[ecu_number].ecu_name} IS NOT WORKING ANY MORE AND VEHICLE IS DISABLED, CONTACT COMPANY TO FIX PROBLEM")
            self.current_download.status = ClientDownloadStatus.FAILED
            self.status = ClientStatus.OFFLINE
            self.state = OfflineState(self)
            self.db.save_download_request(self.current_download)
            raise Exception('CAR SYSTEM FAILED')

        if (self.current_download.flashed_ecus[ecu_number].flashing_retries >= 3) and (self.current_download.flashed_ecus[ecu_number].roll_back_needed == False):
            logging.info(f"ECU: {self.current_download.flashed_ecus[ecu_number].ecu_name} failed to flash the new update")
            logging.info(f"ECU: {self.current_download.flashed_ecus[ecu_number].ecu_name} reached maximum tries of failure to update, so ECU will be kept on current version")
            self.current_download.flashed_ecus[ecu_number].roll_back_needed = True
            self.current_download.flashed_ecus[ecu_number].roll_back_done = True
            logging.info(f"Trying to flash the next ECU that needs to be updated: {(self.current_download.flashed_ecus[self.current_download.flashed_order_index].ecu_name)}")
            self.handle_successful_flashing(ecu_number)
            return

        logging.info(f"Trying try number: {self.current_download.flashed_ecus[ecu_number].flashing_retries+1} to flash ECU: {self.current_download.flashed_ecus[ecu_number].ecu_name}")
        self.UDS_flash()
    
    def receive_message(self) -> Optional[Dict]:
        """Receive and parse a message from the server"""
        try:
            # First receive message length (10 bytes)
            length_data = b""
            while len(length_data) < 10:
                chunk = self.socket.recv(10 - len(length_data))
                if not chunk:
                    logging.error("Connection closed by peer while receiving message length")
                    return None
                length_data += chunk
            
            message_length = int(length_data.decode())
            
            # Receive the actual message
            message_data = b""
            while len(message_data) < message_length:
                remaining = message_length - len(message_data)
                chunk = self.socket.recv(min(self.chunk_size, remaining))
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
    
    def cleanup_connection(self):
        """Clean up socket connection"""
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def shutdown(self):
        """Shutdown the client"""
        self.running = False
        self.cleanup_connection()
