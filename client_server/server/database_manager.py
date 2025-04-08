import json
import os
from typing import Dict, List, Optional
from models import CarType, ECU, Version

class DatabaseManager:
    def __init__(self, data_directory: str):
        self.data_directory = data_directory
        self.car_types_file = os.path.join(data_directory, "car_types.json")
        self.ecus_file = os.path.join(data_directory, "ecus.json")
        self.versions_file = os.path.join(data_directory, "versions.json")

    def load_all_data(self) -> List[CarType]:
        """Load all data from files and create CarType objects"""
        try:
            # Load raw data from files
            with open(self.car_types_file, 'r') as f:
                car_types_data = json.load(f)
            with open(self.ecus_file, 'r') as f:
                ecus_data = json.load(f)
            with open(self.versions_file, 'r') as f:
                versions_data = json.load(f)

            # Process and create objects
            car_types = []
            for car_type_info in car_types_data:
                ecus = []
                for ecu_id in car_type_info['ecu_ids']:
                    ecu_info = next((e for e in ecus_data if e['id'] == ecu_id), None)
                    if ecu_info:
                        versions = []
                        for version_id in ecu_info['version_ids']:
                            version_info = next((v for v in versions_data if v['id'] == version_id), None)
                            if version_info:
                                versions.append(Version(
                                    version_number=version_info['version_number'],
                                    compatible_car_types=version_info['compatible_car_types'],
                                    hex_file_path=version_info['hex_file_path']
                                ))
                        
                        ecus.append(ECU(
                            name=ecu_info['name'],
                            model_number=ecu_info['model_number'],
                            versions=versions
                        ))

                car_types.append(CarType(
                    name=car_type_info['name'],
                    model_number=car_type_info['model_number'],
                    ecus=ecus,
                    manufactured_count=car_type_info['manufactured_count'],
                    car_ids=car_type_info['car_ids']
                ))

            return car_types

        except Exception as e:
            print(f"Error loading database: {str(e)}")
            return []

    def get_hex_file_chunk(self, file_path: str, chunk_size: int, offset: int) -> Optional[bytes]:
        """Read a chunk of hex file"""
        try:
            with open(file_path, 'rb') as f:
                f.seek(offset)
                return f.read(chunk_size)
        except Exception as e:
            print(f"Error reading hex file: {str(e)}")
            return None

    def get_file_size(self, file_path: str) -> int:
        """Get size of a hex file"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            print(f"Error getting file size: {str(e)}")
            return 0