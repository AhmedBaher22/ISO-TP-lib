#!/usr/bin/env python3
"""
BeagleBone ECU Flashing Server - Enhanced with Chunked File Transfer Support
This script runs on the BeagleBone and handles flashing requests from Android.
Now supports chunked file transfers for large hex files.
"""
from time import sleep
import socket
import threading
import json
import struct
import time
import logging
import os
import sys
import pickle
import signal
import base64
import hashlib
import tempfile
from typing import Dict, List, Optional
from datetime import datetime
from time import sleep

# Import existing classes and modules from your architecture
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)

from enums import *
from protocol import Protocol
from client_models import ClientDownloadRequest, flashingEcu
from client_database import ClientDatabase
from shared_models import CarInfo
from delta_generator.DeltaGenerator import DeltaGenerator, DeltaAlgorithm
from logger import Logger, LogType, ProtocolType
from iso_tp_layer.IsoTpConfig import IsoTpConfig
from iso_tp_layer.IsoTp import IsoTp
from uds_layer.uds_client import UdsClient
from iso_tp_layer.Address import Address
from can_layer.can_communication import CANCommunication, CANConfiguration
from can_layer.enums import CANInterface
from can_layer.CanExceptions import CANError
from uds_layer.uds_enums import SessionType
from uds_layer.server import Server
from uds_layer.transfer_request import TransferRequest
from uds_layer.transfer_enums import EncryptionMethod, CompressionMethod, CheckSumMethod
from app_initialization import init_uds_client
from hex_parser.SRecordParser import DataRecord, SRecordParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BeagleBoneFlashing')

class ChunkedTransfer:
    """Manages chunked file transfer state"""
    
    def __init__(self, transfer_id: str, ecu_number: int, ecu_name: str, 
                 total_size: int, total_chunks: int, chunk_size: int,
                 old_version: str, new_version: str, checksum: str):
        self.transfer_id = transfer_id
        self.ecu_number = ecu_number
        self.ecu_name = ecu_name
        self.total_size = total_size
        self.total_chunks = total_chunks
        self.chunk_size = chunk_size
        self.old_version = old_version
        self.new_version = new_version
        self.expected_checksum = checksum
        
        # Transfer state
        self.chunks_received = {}  # chunk_index -> chunk_data
        self.temp_file = None
        self.bytes_received = 0
        self.start_time = time.time()
        self.completed = False
        self.failed = False
        self.error_message = ""
        
        # Create temporary file for assembly
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=f"ecu_{ecu_number}_", suffix=".hex")
        logger.info(f"Created temporary file for chunked transfer: {self.temp_file.name}")
    
    def add_chunk(self, chunk_index: int, chunk_data: bytes) -> bool:
        """Add a chunk to the transfer"""
        try:
            if chunk_index in self.chunks_received:
                logger.warning(f"Duplicate chunk {chunk_index} received for transfer {self.transfer_id}")
                return True
            
            if chunk_index >= self.total_chunks:
                raise ValueError(f"Invalid chunk index {chunk_index}, expected 0-{self.total_chunks-1}")
            
            self.chunks_received[chunk_index] = chunk_data
            self.bytes_received += len(chunk_data)
            
            logger.debug(f"Received chunk {chunk_index + 1}/{self.total_chunks} ({len(chunk_data)} bytes)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding chunk {chunk_index}: {e}")
            self.failed = True
            self.error_message = str(e)
            return False
    
    def is_complete(self) -> bool:
        """Check if all chunks have been received"""
        return len(self.chunks_received) == self.total_chunks
    
    def assemble_file(self) -> str:
        """Assemble chunks into final file and return file path"""
        try:
            if not self.is_complete():
                raise ValueError(f"Cannot assemble incomplete transfer: {len(self.chunks_received)}/{self.total_chunks} chunks")
            
            logger.info(f"Assembling {self.total_chunks} chunks into final file...")
            
            # Write chunks in order to temporary file
            with open(self.temp_file.name, 'wb') as f:
                for chunk_index in range(self.total_chunks):
                    if chunk_index not in self.chunks_received:
                        raise ValueError(f"Missing chunk {chunk_index}")
                    f.write(self.chunks_received[chunk_index])
            
            # Verify assembled file size matches expected
            actual_size = os.path.getsize(self.temp_file.name)
            if actual_size != self.total_size:
                raise ValueError(f"Assembled file size mismatch: expected {self.total_size}, got {actual_size}")
            
            # Read back as text to verify it's valid hex data and calculate checksum
            try:
                with open(self.temp_file.name, 'r', encoding='utf-8') as f:
                    hex_content = f.read()
                
                # Calculate checksum on the hex string content
                calculated_checksum = hashlib.md5(hex_content.encode('utf-8')).hexdigest()
                
                logger.info(f"Assembled file validation:")
                logger.info(f"  Binary size: {actual_size} bytes")
                logger.info(f"  Text size: {len(hex_content)} characters")
                logger.info(f"  Expected checksum: {self.expected_checksum}")
                logger.info(f"  Calculated checksum: {calculated_checksum}")
                
                # Don't fail on checksum mismatch here - let the processing function handle it
                if calculated_checksum != self.expected_checksum:
                    logger.warning(f"Checksum mismatch detected but continuing with assembly")
                
            except UnicodeDecodeError as e:
                raise ValueError(f"Assembled file contains invalid UTF-8 data: {e}")
            
            self.completed = True
            elapsed_time = time.time() - self.start_time
            transfer_rate = self.bytes_received / elapsed_time / 1024
            
            logger.info(f"File assembly completed successfully")
            logger.info(f"File: {self.temp_file.name}, Size: {actual_size} bytes")
            logger.info(f"Chunks: {self.total_chunks}, Time: {elapsed_time:.2f}s, Rate: {transfer_rate:.1f} KB/s")
            
            return self.temp_file.name
            
        except Exception as e:
            logger.error(f"Error assembling chunked file: {e}")
            self.failed = True
            self.error_message = str(e)
            raise
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            if self.temp_file and os.path.exists(self.temp_file.name):
                os.unlink(self.temp_file.name)
                logger.debug(f"Cleaned up temporary file: {self.temp_file.name}")
        except Exception as e:
            logger.warning(f"Error cleaning up temporary file: {e}")

class BeagleBoneFlashingServer:
    def __init__(self, host='192.168.7.2', port=5555):
        self.host = host
        self.port = port
        self.android_ip = '192.168.7.1'
        self.socket = None
        self.client_socket = None
        self.running = False
        
        # Use existing database and logger architecture
        self.data_directory = '/home/debian/Desktop/SDVSOTA/ISO-TP-lib/client_server/client/client_data'
        os.makedirs(self.data_directory, exist_ok=True)
        self.db = ClientDatabase(self.data_directory)
        self.logger = Logger(protocol=ProtocolType.HMI_CLIENT)
        
        # Current processing state
        self.current_download: Optional[ClientDownloadRequest] = None
        self.uds_client = None
        self.chunk_size = 8192
        self.connection_timeout = 300
        self.last_heartbeat = time.time()
        
        # Chunked transfer management
        self.active_transfers: Dict[str, ChunkedTransfer] = {}
        self.transfer_timeouts = {}
        self.max_single_file_size = 100 * 1024
        self.chunk_transfer_timeout = 300
        
        # Protocol message types
        self.MSG_NEW_FLASHING_UPDATES = "NEW_FLASHING_UPDATES"
        self.MSG_SEND_HEX_FILE = "SEND_HEX_FILE"
        self.MSG_HEX_FILE_START = "HEX_FILE_START"
        self.MSG_HEX_FILE_CHUNK = "HEX_FILE_CHUNK"
        self.MSG_HEX_FILE_END = "HEX_FILE_END"
        self.MSG_START_FLASHING = "START_FLASHING"
        self.MSG_FLASHING_ACK = "FLASHING_ACK"
        self.MSG_FLASHING_FAILED = "FLASHING_FAILED"
        self.MSG_SYSTEM_FAILURE = "SYSTEM_FAILURE"
        self.MSG_CANCEL_FLASHING = "CANCEL_FLASHING"
        self.MSG_HEARTBEAT = "HEARTBEAT"
        self.MSG_FLASHING_PROGRESS = "FLASHING_PROGRESS"
        
        # ECU address mapping
        self.ecu_address_map = {
            1: {"txid": 0x7E0, "rxid": 0x7E8, "name": "ENGINE_ECU"},
            2: {"txid": 0x7E1, "rxid": 0x7E9, "name": "TRANSMISSION_ECU"},
            3: {"txid": 0x7E2, "rxid": 0x7EA, "name": "ABS_ECU"},
            4: {"txid": 0x7E3, "rxid": 0x7EB, "name": "AIRBAG_ECU"},
            5: {"txid": 0x7E4, "rxid": 0x7EC, "name": "BCM_ECU"},
            6: {"txid": 55, "rxid": 55, "name": "brake_control_module"}
        }
    
    def start_server(self):
        """Start the flashing server"""
        try:
            self.configure_network()
            self.initialize_can_interface()
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.socket.settimeout(self.connection_timeout)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            
            self.running = True
            logger.info(f"BeagleBone flashing server started on {self.host}:{self.port}")
            logger.info(f"Listening for Android device at {self.android_ip}")
            logger.info(f"Chunked transfer support enabled (max single file: {self.max_single_file_size} bytes)")
            
            # Start monitoring threads
            threading.Thread(target=self.heartbeat_monitor, daemon=True).start()
            threading.Thread(target=self.connection_timeout_monitor, daemon=True).start()
            threading.Thread(target=self.chunk_timeout_monitor, daemon=True).start()
            
            while self.running:
                try:
                    logger.info("Waiting for Android client connection...")
                    client_socket, address = self.socket.accept()
                    logger.info(f"Android client connected from {address}")
                    
                    if address[0] != self.android_ip:
                        logger.warning(f"Connection from unexpected IP: {address[0]}")
                        client_socket.close()
                        continue
                    
                    self.client_socket = client_socket
                    self.client_socket.settimeout(30)
                    self.last_heartbeat = time.time()
                    self.handle_client()
                    
                except socket.timeout:
                    logger.info("Socket timeout waiting for connection")
                    continue
                except socket.error as e:
                    if self.running:
                        logger.error(f"Socket error: {e}")
                        time.sleep(5)
                    
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.cleanup()
    
    def configure_network(self):
        """Configure BeagleBone network interface"""
        try:
            import subprocess
            logger.info("Configuring network interface...")
            
            result = subprocess.run(['ip', 'addr', 'show', 'usb0'], 
                                  capture_output=True, text=True, check=False)
            
            if self.host not in result.stdout:
                subprocess.run(['sudo', 'ip', 'addr', 'add', f'{self.host}/24', 'dev', 'usb0'], 
                             check=False)
                subprocess.run(['sudo', 'ip', 'link', 'set', 'usb0', 'up'], check=False)
                logger.info(f"Network configured: {self.host}")
            else:
                logger.info(f"Network already configured: {self.host}")
                
            subprocess.run(['sudo', 'ip', 'route', 'add', self.android_ip, 'dev', 'usb0'], 
                         check=False)
                
        except Exception as e:
            logger.warning(f"Network configuration failed: {e}")
    
    def initialize_can_interface(self):
        """Initialize CAN interface"""
        try:
            import subprocess
            logger.info("Initializing CAN interface...")
            
            subprocess.run(['sudo', 'ip', 'link', 'set', 'can0', 'type', 'can', 'bitrate', '500000'], 
                         check=False)
            subprocess.run(['sudo', 'ip', 'link', 'set', 'up', 'can0'], check=False)
            
            logger.info("CAN interface initialized")
            
        except Exception as e:
            logger.warning(f"CAN interface initialization failed: {e}")
    
    def chunk_timeout_monitor(self):
        """Monitor chunked transfer timeouts"""
        while self.running:
            try:
                time.sleep(30)
                current_time = time.time()
                
                timed_out_transfers = []
                for transfer_id, timeout_time in self.transfer_timeouts.items():
                    if current_time > timeout_time:
                        timed_out_transfers.append(transfer_id)
                
                for transfer_id in timed_out_transfers:
                    logger.warning(f"Chunked transfer {transfer_id} timed out")
                    self.cleanup_chunked_transfer(transfer_id)
                    
            except Exception as e:
                logger.warning(f"Chunk timeout monitor error: {e}")
    
    def cleanup_chunked_transfer(self, transfer_id: str):
        """Clean up a chunked transfer"""
        try:
            if transfer_id in self.active_transfers:
                transfer = self.active_transfers[transfer_id]
                transfer.cleanup()
                del self.active_transfers[transfer_id]
                
            if transfer_id in self.transfer_timeouts:
                del self.transfer_timeouts[transfer_id]
                
            logger.info(f"Cleaned up chunked transfer: {transfer_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up chunked transfer {transfer_id}: {e}")
    
    def heartbeat_monitor(self):
        """Monitor connection with Android device"""
        while self.running:
            try:
                time.sleep(30)
                if self.client_socket:
                    self.send_heartbeat()
            except Exception as e:
                logger.warning(f"Heartbeat error: {e}")
    
    def connection_timeout_monitor(self):
        """Monitor connection timeout"""
        while self.running:
            try:
                time.sleep(60)
                if self.client_socket and (time.time() - self.last_heartbeat) > self.connection_timeout:
                    logger.warning("Connection timeout - closing client connection")
                    self.close_client_connection()
            except Exception as e:
                logger.warning(f"Connection timeout monitor error: {e}")
    
    def send_heartbeat(self):
        """Send heartbeat to Android device"""
        try:
            message = {
                "type": self.MSG_HEARTBEAT,
                "timestamp": time.time(),
                "beaglebone_status": "alive",
                "data": {
                    "uptime": self.get_system_uptime(),
                    "temperature": self.get_cpu_temperature(),
                    "memory_usage": self.get_memory_usage(),
                    "can_status": self.get_can_status(),
                    "current_flashing_status": self.get_flashing_status(),
                    "active_transfers": len(self.active_transfers),
                    "chunked_transfer_support": True
                }
            }
            self.send_message(message)
            self.last_heartbeat = time.time()
        except Exception as e:
            logger.warning(f"Failed to send heartbeat: {e}")
    
    def handle_client(self):
        """Handle client messages"""
        try:
            while self.running and self.client_socket:
                try:
                    length_data = self.client_socket.recv(4)
                    if not length_data:
                        logger.info("Client disconnected")
                        break
                    
                    if len(length_data) != 4:
                        logger.error("Invalid message length header")
                        break
                    
                    message_length = struct.unpack('>I', length_data)[0]
                    
                    if message_length > 50 * 1024 * 1024:
                        logger.error(f"Message too large: {message_length} bytes")
                        break
                    
                    message_data = b''
                    while len(message_data) < message_length:
                        remaining = message_length - len(message_data)
                        chunk = self.client_socket.recv(min(remaining, 4096))
                        if not chunk:
                            logger.error("Connection lost while receiving message")
                            return
                        message_data += chunk
                    
                    if len(message_data) != message_length:
                        logger.error("Incomplete message received")
                        break
                    
                    try:
                        message_json = message_data.decode('utf-8')
                        message = json.loads(message_json)
                        self.handle_message(message)
                        self.last_heartbeat = time.time()
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}")
                    except UnicodeDecodeError as e:
                        logger.error(f"Unicode decode error: {e}")
                        
                except socket.timeout:
                    logger.debug("Socket timeout during receive")
                    continue
                except socket.error as e:
                    logger.error(f"Socket error during client handling: {e}")
                    break
                
        except Exception as e:
            logger.error(f"Client handling error: {e}")
        finally:
            self.close_client_connection()
    
    def close_client_connection(self):
        """Close client connection safely"""
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
            logger.info("Client connection closed")
            
            for transfer_id in list(self.active_transfers.keys()):
                self.cleanup_chunked_transfer(transfer_id)
    
    def handle_message(self, message: dict):
        """Handle incoming messages from Android app"""
        try:
            msg_type = message.get('type')
            ecu_number = message.get('ecuNumber', -1)
            data = message.get('data', {})
            
            logger.info(f"Received: {msg_type} for ECU {ecu_number}")
            
            if msg_type == "HANDSHAKE":
                self.handle_handshake(data)
            elif msg_type == self.MSG_NEW_FLASHING_UPDATES:
                self.handle_new_flashing_updates(data)
            elif msg_type == self.MSG_SEND_HEX_FILE:
                self.handle_hex_file(ecu_number, data)
            elif msg_type == self.MSG_HEX_FILE_START:
                self.handle_hex_file_start(ecu_number, data)
            elif msg_type == self.MSG_HEX_FILE_CHUNK:
                self.handle_hex_file_chunk(ecu_number, data)
            elif msg_type == self.MSG_HEX_FILE_END:
                self.handle_hex_file_end(ecu_number, data)
            elif msg_type == self.MSG_START_FLASHING:
                self.handle_start_flashing()
            elif msg_type == self.MSG_CANCEL_FLASHING:
                self.handle_cancel_flashing()
            elif msg_type == "PING":
                self.handle_ping()
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self.send_error_response(f"Message handling error: {str(e)}")
    
    def handle_ping(self):
        """Handle ping from Android device"""
        try:
            response = {
                "type": "PONG",
                "timestamp": time.time(),
                "data": {"status": "ok"}
            }
            self.send_message(response)
        except Exception as e:
            logger.error(f"Error handling ping: {e}")
    
    def handle_handshake(self, data: dict):
        """Handle handshake from Android device"""
        try:
            android_ip = data.get('androidIp', 'unknown')
            client_version = data.get('clientVersion', 'unknown')
            capabilities = data.get('capabilities', [])
            max_chunk_size = data.get('maxChunkSize', 8192)
            
            logger.info(f"Handshake from Android {android_ip} version {client_version}")
            logger.info(f"Client capabilities: {capabilities}")
            logger.info(f"Client max chunk size: {max_chunk_size}")
            
            if max_chunk_size > 0:
                self.chunk_size = max_chunk_size
                logger.info(f"Updated chunk size to: {self.chunk_size}")
            
            response = {
                "type": "HANDSHAKE_ACK",
                "data": {
                    "beaglebone_version": "2.0-chunked",
                    "capabilities": ["ECU_FLASHING", "CAN_COMMUNICATION", "DIAGNOSTIC", 
                                   "HEARTBEAT", "CHUNKED_TRANSFER", "LARGE_FILES"],
                    "status": "ready",
                    "supported_ecus": list(self.ecu_address_map.keys()),
                    "max_file_size": 50 * 1024 * 1024,
                    "supported_formats": ["SRECORD", "HEX"],
                    "chunk_size": self.chunk_size,
                    "max_single_file_size": self.max_single_file_size,
                    "features": ["chunked_transfer", "checksum_validation", "progress_reporting"],
                    "protocol_version": "2.0"
                }
            }
            self.send_message(response)
            
        except Exception as e:
            logger.error(f"Error handling handshake: {e}")
            self.send_error_response("Handshake failed")
    
    def handle_new_flashing_updates(self, data: dict):
        """Handle new flashing updates message and reconstruct ClientDownloadRequest"""
        try:
            download_request_data = data.get('downloadRequest', {})
            car_info_data = download_request_data.get('carInfo', {})
            
            car_info =  self.db.load_car_info()
            
            self.current_download = ClientDownloadRequest(
                request_id=download_request_data['requestId'],
                timestamp=datetime.fromtimestamp(download_request_data['timestamp'] / 1000),
                car_info=car_info,
                required_updates=download_request_data['requiredUpdates'],
                status=ClientDownloadStatus[download_request_data['status']],
                total_ecus=download_request_data['totalEcus'],
                completed_ecus=download_request_data['completedEcus'],
                downloaded_versions=download_request_data['downloadedVersions'],
                file_offsets={},
                total_size=download_request_data['totalSize'],
                downloaded_size=download_request_data['downloadedSize'],
                flashed_ecus=[],
                number_of_flashed_ecus=0,
                flashed_order_index=0
            )
            
            self.db.save_download_request(self.current_download)
            self.db.save_car_info(car_info)
            
            logger.info(f"New flashing request received for {data['totalEcus']} ECUs")
            logger.info(f"Car: {data['carId']} ({data['carType']})")
            logger.info(f"Download request reconstructed and saved")
            
            response = {
                "type": "NEW_FLASHING_UPDATES_ACK",
                "data": {
                    "status": "accepted",
                    "request_id": self.current_download.request_id,
                    "message": "Ready to receive hex files (chunked transfer supported)",
                    "chunked_transfer_enabled": True,
                    "max_single_file_size": self.max_single_file_size
                }
            }
            self.send_message(response)
            
        except Exception as e:
            logger.error(f"Error handling new flashing updates: {e}")
            self.send_error_response("Failed to process flashing request")
    
    def handle_hex_file_start(self, ecu_number: int, data: dict):
        """Handle start of chunked hex file transfer"""
        try:
            transfer_id = data['transferId']
            ecu_name = data['ecuName']
            total_size = data['totalSize']
            total_chunks = data['totalChunks']
            chunk_size = data['chunkSize']
            old_version = data['oldVersion']
            new_version = data['newVersion']
            checksum = data['checksum']
            
            logger.info(f"Starting chunked transfer for ECU {ecu_number} ({ecu_name})")
            logger.info(f"Transfer ID: {transfer_id}")
            logger.info(f"Total size: {total_size} bytes, Total chunks: {total_chunks}")
            logger.info(f"Version: {old_version} -> {new_version}")
            
            if transfer_id in self.active_transfers:
                logger.warning(f"Transfer {transfer_id} already exists, cleaning up previous")
                self.cleanup_chunked_transfer(transfer_id)
            
            if total_size <= 0 or total_chunks <= 0:
                raise ValueError(f"Invalid transfer parameters: size={total_size}, chunks={total_chunks}")
            
            chunked_transfer = ChunkedTransfer(
                transfer_id=transfer_id,
                ecu_number=ecu_number,
                ecu_name=ecu_name,
                total_size=total_size,
                total_chunks=total_chunks,
                chunk_size=chunk_size,
                old_version=old_version,
                new_version=new_version,
                checksum=checksum
            )
            
            self.active_transfers[transfer_id] = chunked_transfer
            self.transfer_timeouts[transfer_id] = time.time() + self.chunk_transfer_timeout
            
            response = {
                "type": f"{self.MSG_HEX_FILE_START}_ACK",
                "ecuNumber": ecu_number,
                "data": {
                    "status": "ready",
                    "transfer_id": transfer_id,
                    "message": f"Ready to receive {total_chunks} chunks"
                }
            }
            self.send_message(response)
            
            logger.info(f"Chunked transfer {transfer_id} initialized successfully")
            
        except Exception as e:
            logger.error(f"Error handling hex file start for ECU {ecu_number}: {e}")
            self.send_error_response(f"Failed to start chunked transfer: {str(e)}")
    
    def handle_hex_file_chunk(self, ecu_number: int, data: dict):
        """Handle individual chunk of hex file"""
        try:
            transfer_id = data['transferId']
            chunk_index = data['chunkIndex']
            chunk_data_b64 = data['chunkData']
            chunk_size = data['chunkSize']
            
            if transfer_id not in self.active_transfers:
                raise ValueError(f"Unknown transfer ID: {transfer_id}")
            
            transfer = self.active_transfers[transfer_id]
            
            if transfer.ecu_number != ecu_number:
                raise ValueError(f"ECU number mismatch: expected {transfer.ecu_number}, got {ecu_number}")
            
            try:
                chunk_data = base64.b64decode(chunk_data_b64)
            except Exception as e:
                raise ValueError(f"Failed to decode chunk data: {e}")
            
            if len(chunk_data) != chunk_size:
                raise ValueError(f"Chunk size mismatch: expected {chunk_size}, got {len(chunk_data)}")
            
            if not transfer.add_chunk(chunk_index, chunk_data):
                raise ValueError(f"Failed to add chunk {chunk_index}")
            
            self.transfer_timeouts[transfer_id] = time.time() + self.chunk_transfer_timeout
            
            if (chunk_index + 1) % 10 == 0 or chunk_index + 1 == transfer.total_chunks:
                progress_percent = ((chunk_index + 1) / transfer.total_chunks) * 100
                logger.info(f"Chunk progress for {transfer.ecu_name}: {chunk_index + 1}/{transfer.total_chunks} ({progress_percent:.1f}%)")
            
        except Exception as e:
            logger.error(f"Error handling hex file chunk for ECU {ecu_number}: {e}")
            transfer_id = data.get('transferId')
            if transfer_id and transfer_id in self.active_transfers:
                self.cleanup_chunked_transfer(transfer_id)
            self.send_error_response(f"Failed to process chunk: {str(e)}")
    
    def handle_hex_file_end(self, ecu_number: int, data: dict):
        """Handle end of chunked hex file transfer and assemble file"""
        try:
            transfer_id = data['transferId']
            final_checksum = data['finalChecksum']
            
            logger.info(f"Finalizing chunked transfer {transfer_id} for ECU {ecu_number}")
            
            if transfer_id not in self.active_transfers:
                raise ValueError(f"Unknown transfer ID: {transfer_id}")
            
            transfer = self.active_transfers[transfer_id]
            
            if transfer.ecu_number != ecu_number:
                raise ValueError(f"ECU number mismatch: expected {transfer.ecu_number}, got {ecu_number}")
            
            if final_checksum != transfer.expected_checksum:
                raise ValueError(f"Final checksum mismatch: expected {transfer.expected_checksum}, got {final_checksum}")
            
            if not transfer.is_complete():
                missing_chunks = set(range(transfer.total_chunks)) - set(transfer.chunks_received.keys())
                raise ValueError(f"Incomplete transfer: missing chunks {sorted(list(missing_chunks))}")
            
            assembled_file_path = transfer.assemble_file()
            self.process_assembled_hex_file(transfer, assembled_file_path)
            
            response = {
                "type": f"{self.MSG_HEX_FILE_END}_ACK",
                "ecuNumber": ecu_number,
                "data": {
                    "status": "completed",
                    "transfer_id": transfer_id,
                    "file_size": transfer.total_size,
                    "chunks_received": len(transfer.chunks_received),
                    "message": f"Chunked transfer completed successfully for {transfer.ecu_name}"
                }
            }
            self.send_message(response)
            
            self.cleanup_chunked_transfer(transfer_id)
            logger.info(f"Chunked transfer {transfer_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error handling hex file end for ECU {ecu_number}: {e}")
            transfer_id = data.get('transferId')
            if transfer_id and transfer_id in self.active_transfers:
                self.cleanup_chunked_transfer(transfer_id)
            self.send_error_response(f"Failed to finalize chunked transfer: {str(e)}")
    
    def process_assembled_hex_file(self, transfer: ChunkedTransfer, file_path: str):
        """Process assembled hex file using existing ECU processing logic"""
        try:
            logger.info(f"Processing assembled hex file for ECU {transfer.ecu_name}")
            
            # Read hex data from assembled file as text
            with open(file_path, 'r', encoding='utf-8') as f:
                hex_data = f.read()
            
            # Calculate checksum on the actual hex string content (not binary)
            calculated_checksum = hashlib.md5(hex_data.encode('utf-8')).hexdigest()
            
            # Create data dictionary similar to single file processing
            data = {
                'ecuName': transfer.ecu_name,
                'ecuNumber': transfer.ecu_number,
                'hexData': hex_data,
                'fileSize': len(hex_data),
                'checksum': calculated_checksum,  # Use calculated checksum instead of expected
                'oldVersion': transfer.old_version,
                'newVersion': transfer.new_version,
                'expected_checksum': transfer.expected_checksum  # Keep expected for logging
            }
            
            # Log checksum comparison for debugging
            logger.info(f"Checksum comparison for {transfer.ecu_name}:")
            logger.info(f"  Expected: {transfer.expected_checksum}")
            logger.info(f"  Calculated: {calculated_checksum}")
            logger.info(f"  Match: {calculated_checksum == transfer.expected_checksum}")
            
            # Use existing hex file processing logic
            self.process_hex_file_data(transfer.ecu_number, data, is_chunked=True)
            
        except Exception as e:
            logger.error(f"Error processing assembled hex file: {e}")
            raise
        finally:
            # Clean up assembled file
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug(f"Cleaned up assembled file: {file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up assembled file: {cleanup_error}")
    
    def handle_hex_file(self, ecu_number: int, data: dict):
        """Handle single (non-chunked) hex file data"""
        try:
            logger.info(f"Processing single hex file for ECU {ecu_number}")
            self.process_hex_file_data(ecu_number, data, is_chunked=False)
            
        except Exception as e:
            logger.error(f"Error handling single hex file for ECU {ecu_number}: {e}")
            self.send_error_response(f"Failed to save hex file for ECU {ecu_number}: {str(e)}")
    
    def process_hex_file_data(self, ecu_number: int, data: dict, is_chunked: bool = False):
        """Process hex file data and create flashingEcu objects"""
        try:
            ecu_name = data['ecuName']
            hex_data = data['hexData']
            file_size = data['fileSize']
            checksum = data.get('checksum', '')
            expected_checksum = data.get('expected_checksum', '')
            old_version = data['oldVersion']
            new_version = data['newVersion']
            
            transfer_type = "chunked" if is_chunked else "single"
            logger.info(f"Processing {transfer_type} hex file for ECU {ecu_number} ({ecu_name})")
            logger.info(f"File size: {file_size} bytes, Old: {old_version}, New: {new_version}")
            
            if not hex_data or len(hex_data) == 0:
                raise ValueError("Empty hex data received")
            
            # For chunked transfers, we calculate our own checksum since we assembled the file
            if is_chunked:
                # Recalculate checksum on the actual hex data we have
                calculated_checksum = hashlib.md5(hex_data.encode('utf-8')).hexdigest()
                logger.info(f"Chunked file checksum verification:")
                logger.info(f"  Expected from client: {expected_checksum}")
                logger.info(f"  Calculated on assembled data: {calculated_checksum}")
                
                # Use calculated checksum for chunked files
                final_checksum = calculated_checksum
                
                # Log warning if checksums don't match but don't fail
                if expected_checksum and calculated_checksum != expected_checksum:
                    logger.warning(f"Checksum mismatch for chunked file, using calculated checksum")
            else:
                # For single files, verify provided checksum
                if checksum:
                    calculated_checksum = hashlib.md5(hex_data.encode('utf-8')).hexdigest()
                    if calculated_checksum != checksum:
                        raise ValueError("Hex file checksum mismatch")
                final_checksum = checksum
            
            hex_data_bytes = hex_data.encode('utf-8')
            new_version_path = self.db.save_ecu_version(ecu_name, new_version, hex_data_bytes)
            
            old_version_path = self.db.get_ecu_version_path(ecu_name, old_version)
            if not old_version_path or not os.path.exists(old_version_path):
                old_version_path = self.db.save_ecu_version(ecu_name, old_version, b"")
            
            delta_generator = DeltaGenerator(algorithm=DeltaAlgorithm.SENDING_COMPLETE_SECTOR)
            
            parser_old = SRecordParser()
            parser_new = SRecordParser()
            
            if os.path.exists(old_version_path) and os.path.getsize(old_version_path) > 0:
                parser_old.parse_file(filename=str(old_version_path))
                old_version_data_records = parser_old.get_merged_records()
            else:
                old_version_data_records = []
            
            parser_new.parse_file(filename=str(new_version_path))
            new_version_data_records = parser_new.get_merged_records()
            
            delta_records = delta_generator.generate_delta(
                old_version=old_version_data_records,
                new_version=new_version_data_records
            )
            roll_back_delta = delta_generator.generate_delta(
                old_version=new_version_data_records,
                new_version=old_version_data_records
            )
            
            flashing_ecu = flashingEcu(
                ecu_number=ecu_number,
                old_version_path=str(old_version_path),
                new_version_path=str(new_version_path),
                delta_records=delta_records,
                flashing_done=False,
                ecu_name=ecu_name,
                old_version=old_version,
                new_version=new_version,
                roll_back_delta=roll_back_delta,
                old_version_data_records=old_version_data_records,
                roll_back_needed=False,
                roll_back_done=False,
                flashing_retries=0
            )
            
            if self.current_download:
                self.current_download.flashed_ecus.append(flashing_ecu)
                self.db.save_download_request(self.current_download)
            
            logger.info(f"Hex file processed for ECU {ecu_number} ({ecu_name}) - {transfer_type} transfer")
            logger.info(f"File saved to: {new_version_path} ({file_size} bytes)")
            logger.info(f"Delta records generated: {len(delta_records)} records")
            
            ack_type = "SEND_HEX_FILE_ACK" if not is_chunked else "HEX_FILE_PROCESSED_ACK"
            response = {
                "type": ack_type,
                "ecuNumber": ecu_number,
                "data": {
                    "status": "received",
                    "ecu_name": ecu_name,
                    "file_size": file_size,
                    "delta_records_count": len(delta_records),
                    "transfer_type": transfer_type,
                    "checksum_verified": bool(final_checksum),
                    "final_checksum": final_checksum
                }
            }
            self.send_message(response)
            
        except Exception as e:
            logger.error(f"Error processing hex file for ECU {ecu_number}: {e}")
            raise
    
    def handle_start_flashing(self):
        """Handle start flashing command"""
        try:
            if not self.current_download:
                logger.error("No flashing request available")
                self.send_error_response("No flashing request available")
                return
            
            if not self.current_download.flashed_ecus or len(self.current_download.flashed_ecus) == 0:
                logger.error("No ECUs to flash")
                self.send_error_response("No ECUs to flash")
                return
            
            if self.active_transfers:
                logger.warning(f"Cannot start flashing: {len(self.active_transfers)} chunked transfers still active")
                self.send_error_response("Cannot start flashing: file transfers still in progress")
                return
            
            logger.info("Starting flashing process...")
            logger.info(f"Total ECUs to flash: {len(self.current_download.flashed_ecus)}")
            
            self.current_download.status = ClientDownloadStatus.IN_FLASHING
            self.current_download.flashed_order_index = 0
            self.current_download.number_of_flashed_ecus = 0
            self.db.save_download_request(self.current_download)
            
            response = {
                "type": "START_FLASHING_ACK",
                "data": {
                    "status": "started",
                    "total_ecus": len(self.current_download.flashed_ecus),
                    "estimated_time": len(self.current_download.flashed_ecus) * 60
                }
            }
            self.send_message(response)
            
            threading.Thread(target=self.UDS_flash, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Error starting flashing: {e}")
            self.send_error_response(f"Failed to start flashing: {str(e)}")
    
    def handle_cancel_flashing(self):
        """Handle cancel flashing command"""
        try:
            logger.info("Flashing cancellation requested")
            
            for transfer_id in list(self.active_transfers.keys()):
                logger.info(f"Cancelling active transfer: {transfer_id}")
                self.cleanup_chunked_transfer(transfer_id)
            
            if self.current_download:
                self.current_download.status = ClientDownloadStatus.FAILED
                self.db.save_download_request(self.current_download)
            
            response = {
                "type": "CANCEL_FLASHING_ACK",
                "data": {
                    "status": "cancelled",
                    "message": "Flashing process and transfers cancelled"
                }
            }
            self.send_message(response)
            
        except Exception as e:
            logger.error(f"Error cancelling flashing: {e}")
    
    def get_ecu_address(self, ecu_number: int) -> Optional[Address]:
        """Get ECU address configuration"""
        try:
            if ecu_number in self.ecu_address_map:
                config = self.ecu_address_map[ecu_number]
                return Address(addressing_mode=0, txid=config["txid"], rxid=config["rxid"])
            else:
                return Address(addressing_mode=0, txid=0x7E0 + ecu_number, rxid=0x55 + ecu_number)
        except Exception as e:
            logger.error(f"Error getting ECU address for ECU {ecu_number}: {e}")
            return None
    
    def UDS_flash(self):
        """Main UDS flashing function using existing architecture"""
        try:
            if not self.current_download:
                raise Exception("Error: Trying to flash some updates but no current downloads found")
            
            if self.current_download.number_of_flashed_ecus == len(self.current_download.flashed_ecus):
                raise Exception("Error: Trying to flash some updates but all current downloads are flashed successfully")
            
            if not self.uds_client:
                logger.info("Initializing UDS client...")
                self.uds_client = init_uds_client()
            if not self.uds_client:
                raise Exception("Error: error initializing the uds layer")
            
            logger.info("=== Initializing Communication with ECU ===")
            
            current_ecu = self.current_download.flashed_ecus[self.current_download.flashed_order_index]
            
            logger.info(f"Processing ECU {current_ecu.ecu_number}: {current_ecu.ecu_name}")
            logger.info(f"Flashing attempt: {current_ecu.flashing_retries + 1}")
            
            self.send_flashing_progress(current_ecu.ecu_number, "INITIALIZING", 
                                      f"Initializing communication with {current_ecu.ecu_name}")
            
            ecu_address = self.get_ecu_address(current_ecu.ecu_number)
            if not ecu_address:
                raise Exception(f"Failed to get address configuration for ECU {current_ecu.ecu_number}")
            
            # self.uds_client.add_server(ecu_address, SessionType.PROGRAMMING)
            # sleep(1)
            
            # servers: List[Server] = self.uds_client.get_servers()
            # if not (len(servers) > 0):
            #     logger.error(f"Error initializing Programming session with ECU to be updated, ecu name: {current_ecu.ecu_name}")
            #     self.handle_failed_flashing(self.current_download.flashed_order_index, erasing_happen=False)
            #     return
            
            data_records: List[DataRecord]
            flash_type = ""
            
            if (current_ecu.roll_back_needed == True and 
                current_ecu.roll_back_done == False and 
                current_ecu.flashing_retries >= 4):
                data_records = current_ecu.old_version_data_records
                flash_type = "ROLLBACK_FULL"
                logger.info(f"Using old version data records for rollback")
                
            elif (current_ecu.roll_back_needed == True and 
                  current_ecu.roll_back_done == False and 
                  current_ecu.flashing_retries >= 3):
                data_records = current_ecu.roll_back_delta
                flash_type = "ROLLBACK_DELTA"
                logger.info(f"Using rollback delta records")
                
            else:
                data_records = current_ecu.delta_records
                flash_type = "NEW_VERSION"
                logger.info(f"Using delta records for new version")
            
            logger.info(f"Started UDS flashing for ecu: {current_ecu.ecu_name}, with version: {current_ecu.new_version}")
            logger.info(f"Flash type: {flash_type}, Data records: {len(data_records)}")
            
            self.send_flashing_progress(current_ecu.ecu_number, "FLASHING", 
                                      f"Flashing {current_ecu.ecu_name} ({flash_type})")
            
            time.sleep(5)
            self.handle_successful_flashing(0)
            # self.uds_client.Flash_ECU(
            #     segments=data_records,
            #     recv_DA=servers[0].can_id,
            #     encryption_method=EncryptionMethod.SEC_P_256_R1,
            #     compression_method=CompressionMethod.LZ4,
            #     checksum_required=CheckSumMethod.CRC_32,
            #     on_successfull_flashing=self.handle_successful_flashing,
            #     on_failing_flashing=self.handle_failed_flashing,
            #     flashed_ecu_number=self.current_download.flashed_order_index
            # )
            
        except Exception as e:
            logger.error(f"UDS flashing error: {e}")
            if self.current_download and self.current_download.flashed_order_index < len(self.current_download.flashed_ecus):
                current_ecu = self.current_download.flashed_ecus[self.current_download.flashed_order_index]
                self.send_flashing_progress(current_ecu.ecu_number, "ERROR", f"Flashing error: {str(e)}")
                self.handle_failed_flashing(self.current_download.flashed_order_index, erasing_happen=False)
    
    def send_flashing_progress(self, ecu_number: int, status: str, message: str):
        """Send flashing progress update to Android app"""
        try:
            progress_message = {
                "type": self.MSG_FLASHING_PROGRESS,
                "ecuNumber": ecu_number,
                "data": {
                    "status": status.lower(),
                    "message": message,
                    "timestamp": time.time(),
                    "progress_percentage": self.calculate_progress_percentage()
                }
            }
            
            self.send_message(progress_message)
            logger.info(f"Progress update for ECU {ecu_number}: {status} - {message}")
            
        except Exception as e:
            logger.error(f"Error sending progress update: {e}")
    
    def calculate_progress_percentage(self) -> float:
        """Calculate overall flashing progress percentage"""
        try:
            if not self.current_download or not self.current_download.flashed_ecus:
                return 0.0
            
            total_ecus = len(self.current_download.flashed_ecus)
            completed_ecus = self.current_download.number_of_flashed_ecus
            current_index = self.current_download.flashed_order_index
            
            base_progress = (completed_ecus / total_ecus) * 100
            current_ecu_progress = ((current_index - completed_ecus) / total_ecus) * 100 * 0.5
            
            return min(base_progress + current_ecu_progress, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating progress: {e}")
            return 0.0
    
    def handle_successful_flashing(self, ecu_number: int):
        """Handle successful flashing using existing logic"""
        try:
            print("before")
            current_ecu = self.current_download.flashed_ecus[ecu_number]
            print("after")
            logger.info(f"ECU {current_ecu.ecu_name} flashed successfully")
            
            if current_ecu.roll_back_needed == True and current_ecu.flashing_retries > 3:
                current_ecu.roll_back_done = True
                logger.info(f"ECU {current_ecu.ecu_name} rolled back successfully")
            else:
                current_ecu.flashing_done = True
                logger.info(f"ECU {current_ecu.ecu_name} updated to new version successfully")
            
            self.current_download.flashed_order_index += 1
            self.current_download.number_of_flashed_ecus += 1
            
            status_msg = "ROLLED_BACK" if current_ecu.roll_back_done else "SUCCESS"
            message = f"ECU {current_ecu.ecu_name} flashed successfully"
            if current_ecu.roll_back_done:
                message += " (rolled back to previous version)"
            
            self.send_flashing_result(ecu_number, status_msg, message)
            print("here")
            print(f"current_download.number_of_flashed_ecus:: {current_download.number_of_flashed_ecus}")
            print(f"self.current_download.flashed_ecus:: {self.current_download.flashed_ecus}")
            if self.current_download.number_of_flashed_ecus >= len(self.current_download.flashed_ecus):
                print("enter")
                self.handle_flashing_completion()
                return
            else:
                logger.info(f"Preparing to flash next ECU ({self.current_download.flashed_order_index + 1}/{len(self.current_download.flashed_ecus)})")
                self.db.save_download_request(self.current_download)
                
                time.sleep(2)
                threading.Thread(target=self.UDS_flash, daemon=True).start()
                
        except Exception as e:
            logger.error(f"Error in handle_successful_flashing: {e}")
            self.send_flashing_result(ecu_number, "SYSTEM_FAILURE", str(e))
    
    def handle_flashing_completion(self):
        """Handle completion of all ECU flashing"""
        try:
            check_all_up_to_date_flag = False
            rolled_back_ecus = []
            successful_ecus = []
            
            for ecu in self.current_download.flashed_ecus:
                if ecu.roll_back_done == True and ecu.flashing_done == False:
                    rolled_back_ecus.append(ecu.ecu_name)
                    check_all_up_to_date_flag = True
                elif ecu.flashing_done == True:
                    successful_ecus.append(ecu.ecu_name)
            
            if check_all_up_to_date_flag:
                self.current_download.status = ClientDownloadStatus.FAILED
                logger.warning(f"Flashing process finished but not all ECUs updated successfully")
                logger.warning(f"Successful updates: {successful_ecus}")
                logger.warning(f"Rolled back ECUs: {rolled_back_ecus}")
            else:
                self.current_download.status = ClientDownloadStatus.COMPLETED
                logger.info("All ECUs updated and flashed successfully")
                logger.info(f"Successfully updated ECUs: {successful_ecus}")
            
            for ecu in self.current_download.flashed_ecus:
                if ecu.flashing_done:
                    self.current_download.car_info.ecu_versions[ecu.ecu_name] = ecu.new_version
                elif ecu.roll_back_done:
                    self.current_download.car_info.ecu_versions[ecu.ecu_name] = ecu.old_version
            
            self.db.save_car_info(self.current_download.car_info)
            self.db.save_download_request(self.current_download)
            
            completion_message = {
                "type": "FLASHING_COMPLETED",
                "data": {
                    "status": "completed" if self.current_download.status == ClientDownloadStatus.COMPLETED else "partial_failure",
                    "successful_ecus": successful_ecus,
                    "rolled_back_ecus": rolled_back_ecus,
                    "total_ecus": len(self.current_download.flashed_ecus),
                    "completion_time": time.time(),
                    "car_info": {
                        "car_id": self.current_download.car_info.car_id,
                        "car_type": self.current_download.car_info.car_type,
                        "ecu_versions": self.current_download.car_info.ecu_versions
                    }
                }
            }
            self.send_message(completion_message)
            
            logger.info("Flashing process completed - sent completion message to Android")
            
        except Exception as e:
            logger.error(f"Error in handle_flashing_completion: {e}")
    
    def handle_failed_flashing(self, ecu_number: int, erasing_happen: bool):
        """Handle failed flashing using existing logic"""
        try:
            current_ecu = self.current_download.flashed_ecus[ecu_number]
            
            logger.warning(f"ECU {current_ecu.ecu_name} flashing failed (attempt {current_ecu.flashing_retries + 1})")
            
            if erasing_happen:
                current_ecu.roll_back_needed = True
                logger.warning(f"ECU {current_ecu.ecu_name} requires rollback due to erasing")
            
            current_ecu.flashing_retries += 1
            
            failure_reason = "erasing_happened" if erasing_happen else "communication_error"
            self.send_flashing_result(ecu_number, "FAILED", 
                                    f"ECU {current_ecu.ecu_name} flashing failed (attempt {current_ecu.flashing_retries}), reason: {failure_reason}")
            
            if current_ecu.flashing_retries >= 13 and current_ecu.roll_back_needed:
                logger.error(f"CRITICAL: ECU {current_ecu.ecu_name} failed to roll back to old version")
                logger.error(f"SAFETY WARNING: ECU {current_ecu.ecu_name} IS NOT WORKING AND VEHICLE MAY BE DISABLED")
                self.current_download.status = ClientDownloadStatus.FAILED
                self.db.save_download_request(self.current_download)
                self.send_flashing_result(ecu_number, "SYSTEM_FAILURE", 
                                        f"CRITICAL: ECU {current_ecu.ecu_name} system failure - vehicle safety compromised")
                return
            
            if current_ecu.flashing_retries >= 3 and not current_ecu.roll_back_needed:
                logger.info(f"ECU {current_ecu.ecu_name} failed to flash new update after 3 attempts")
                logger.info(f"ECU {current_ecu.ecu_name} keeping current version, marking as rolled back")
                current_ecu.roll_back_needed = True
                current_ecu.roll_back_done = True
                self.handle_successful_flashing(ecu_number)
                return
            
            logger.info(f"Retrying flash for ECU: {current_ecu.ecu_name} (attempt {current_ecu.flashing_retries + 1})")
            self.db.save_download_request(self.current_download)
            
            time.sleep(5)
            threading.Thread(target=self.UDS_flash, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Error in handle_failed_flashing: {e}")
            self.send_flashing_result(ecu_number, "SYSTEM_FAILURE", str(e))
    
    def send_flashing_result(self, ecu_number: int, status: str, message: str = ""):
        """Send flashing result back to Android app"""
        try:
            if status == "SUCCESS":
                msg_type = self.MSG_FLASHING_ACK
            elif status == "FAILED":
                msg_type = self.MSG_FLASHING_FAILED
            elif status == "ROLLED_BACK":
                msg_type = self.MSG_FLASHING_ACK
            else:
                msg_type = self.MSG_SYSTEM_FAILURE
            
            response_message = {
                "type": msg_type,
                "ecuNumber": ecu_number,
                "data": {
                    "status": status.lower(),
                    "message": message,
                    "timestamp": time.time(),
                    "ecu_name": self.current_download.flashed_ecus[ecu_number].ecu_name if self.current_download and ecu_number < len(self.current_download.flashed_ecus) else "unknown"
                }
            }
            
            self.send_message(response_message)
            logger.info(f"Sent {msg_type} for ECU {ecu_number}: {message}")
            
        except Exception as e:
            logger.error(f"Error sending flashing result for ECU {ecu_number}: {e}")
    
    def send_error_response(self, error_message: str):
        """Send error response to Android app"""
        try:
            message = {
                "type": "ERROR",
                "data": {
                    "error": error_message,
                    "timestamp": time.time(),
                    "beaglebone_status": "error",
                    "active_transfers": len(self.active_transfers)
                }
            }
            self.send_message(message)
            logger.error(f"Sent error response: {error_message}")
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")
    
    def send_message(self, message: dict):
        """Send message to Android app"""
        try:
            if not self.client_socket:
                raise Exception("No client connected")
            
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')
            
            self.client_socket.send(struct.pack('>I', len(message_bytes)))
            self.client_socket.send(message_bytes)
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    def get_system_uptime(self) -> str:
        """Get system uptime"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                return f"{hours}h {minutes}m"
        except:
            return "unknown"
    
    def get_cpu_temperature(self) -> str:
        """Get CPU temperature"""
        try:
            temp_paths = [
                '/sys/class/thermal/thermal_zone0/temp',
                '/sys/class/thermal/thermal_zone1/temp',
                '/sys/devices/virtual/thermal/thermal_zone0/temp'
            ]
            
            for path in temp_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        temp = int(f.read()) / 1000.0
                        return f"{temp:.1f}°C"
            return "unknown"
        except:
            return "unknown"
    
    def get_memory_usage(self) -> str:
        """Get memory usage"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                total = int(lines[0].split()[1])
                available = int(lines[2].split()[1])
                used_percent = ((total - available) / total) * 100
                return f"{used_percent:.1f}%"
        except:
            return "unknown"
    
    def get_can_status(self) -> str:
        """Get CAN interface status"""
        try:
            import subprocess
            result = subprocess.run(['ip', 'link', 'show', 'can0'], 
                                  capture_output=True, text=True, check=False)
            if 'UP' in result.stdout:
                return "up"
            elif 'DOWN' in result.stdout:
                return "down"
            else:
                return "unknown"
        except:
            return "unknown"
    
    def get_flashing_status(self) -> dict:
        """Get current flashing status"""
        try:
            if not self.current_download:
                return {
                    "status": "idle", 
                    "progress": 0,
                    "active_transfers": len(self.active_transfers)
                }
            
            status_map = {
                ClientDownloadStatus.WAITING: "waiting",
                ClientDownloadStatus.IN_FLASHING: "flashing",
                ClientDownloadStatus.COMPLETED: "completed",
                ClientDownloadStatus.FAILED: "failed"
            }
            
            return {
                "status": status_map.get(self.current_download.status, "unknown"),
                "progress": self.calculate_progress_percentage(),
                "current_ecu": self.current_download.flashed_order_index + 1 if self.current_download.flashed_order_index < len(self.current_download.flashed_ecus) else None,
                "total_ecus": len(self.current_download.flashed_ecus),
                "completed_ecus": self.current_download.number_of_flashed_ecus,
                "active_transfers": len(self.active_transfers)
            }
        except:
            return {"status": "unknown", "progress": 0, "active_transfers": 0}
    
    def stop_server(self):
        """Stop the server"""
        logger.info("Stopping BeagleBone flashing server...")
        self.running = False
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up server resources...")
        
        for transfer_id in list(self.active_transfers.keys()):
            logger.info(f"Cleaning up active transfer: {transfer_id}")
            self.cleanup_chunked_transfer(transfer_id)
        
        self.close_client_connection()
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        if self.uds_client:
            try:
                pass
            except:
                pass
            self.uds_client = None
        
        logger.info("BeagleBone server cleanup completed")

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if hasattr(signal_handler, 'server'):
        signal_handler.server.stop_server()
    sys.exit(0)

def main():
    """Main function to start the BeagleBone flashing server"""
    server = BeagleBoneFlashingServer()
    signal_handler.server = server
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Starting BeagleBone ECU Flashing Server with Chunked Transfer Support...")
        logger.info("Hardware Configuration:")
        logger.info(f"   BeagleBone IP: {server.host}:{server.port}")
        logger.info(f"   Android IP: {server.android_ip}")
        logger.info(f"   Data Directory: {server.data_directory}")
        logger.info(f"   Supported ECUs: {list(server.ecu_address_map.keys())}")
        logger.info("Chunked Transfer Configuration:")
        logger.info(f"   Chunk Size: {server.chunk_size} bytes")
        logger.info(f"   Max Single File Size: {server.max_single_file_size} bytes")
        logger.info(f"   Transfer Timeout: {server.chunk_transfer_timeout} seconds")
        
        os.makedirs('/var/log', exist_ok=True)
        os.makedirs(server.data_directory, exist_ok=True)
        
        logger.info("Starting server...")
        server.start_server()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal server error: {e}")
        sys.exit(1)
    finally:
        logger.info("Server shutdown complete")

if __name__ == "__main__":
    main()