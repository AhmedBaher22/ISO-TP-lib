import logging
import json
import os
from typing import Optional, Dict
from datetime import datetime
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)

from client_server.client.client_models import ClientDownloadRequest
from client_server.client.shared_models import CarInfo

logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.ERROR)


class ClientDatabase:
    def __init__(self, data_directory: str):
        self.data_directory = data_directory
        self.car_info_file = os.path.join(data_directory, "car_info.json")
        self.download_request_file = os.path.join(data_directory, "download_request.json")
        self.ecu_versions_dir = os.path.join(data_directory, "ecu_versions")
        
        # Create directories if they don't exist
        os.makedirs(self.data_directory, exist_ok=True)
        os.makedirs(self.ecu_versions_dir, exist_ok=True)

    def save_car_info(self, car_info: CarInfo):
        """Save car information to file"""
        with open(self.car_info_file, 'w') as f:
            json.dump({
                'car_type': car_info.car_type,
                'car_name': car_info.car_name,
                'car_model': car_info.car_model,
                'car_id': car_info.car_id,
                'ecu_versions': car_info.ecu_versions
            }, f)

    def load_car_info(self) -> Optional[CarInfo]:
        """Load car information from file"""
        try:
            if os.path.exists(self.car_info_file):
                with open(self.car_info_file, 'r') as f:
                    data = json.load(f)
                    return CarInfo(**data)
            return None
        except Exception as e:
            logging.error(f"Error loading car info: {str(e)}")
            return None

    def save_download_request(self, request: ClientDownloadRequest):
        """Save download request to file"""
        with open(self.download_request_file, 'w') as f:
            json.dump(request.to_dict(), f)

    def load_download_request(self) -> Optional[ClientDownloadRequest]:
        """Load download request from file"""
        try:
            if os.path.exists(self.download_request_file):
                with open(self.download_request_file, 'r') as f:
                    data = json.load(f)

                    return ClientDownloadRequest.from_dict(data)
            return None
        except Exception as e:
            logging.error(f"Error loading download request: {str(e)}")
            return None

    def save_ecu_version(self, ecu_name: str, version: str, hex_data: bytes):
        """Save ECU hex file"""
        # Create the directory path
        dir_path = os.path.join(self.ecu_versions_dir, ecu_name, version)
        os.makedirs(dir_path, exist_ok=True)  # Ensure the directory exists

        # Compose the full file path
        file_name = f"{ecu_name}_v{version}.srec"
        file_path = os.path.join(dir_path, file_name)
        with open(file_path, 'wb') as f:
            f.write(hex_data)
        return file_path

    def get_ecu_version_path(self, ecu_name: str, version: str) -> Optional[str]:
        """Get path to ECU hex file"""
        file_name = f"{ecu_name}_v{version}.srec"
        file_path = os.path.join(self.ecu_versions_dir, ecu_name, version, file_name)
        return file_path if os.path.exists(file_path) else None