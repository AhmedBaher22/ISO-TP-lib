from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class ECUVersion:
    ecu_name: str
    version_number: str
    hex_file_path: Optional[str] = None

@dataclass
class CarInfo:
    car_type: str
    car_name: str
    car_model: str
    car_id: str
    ecu_versions: Dict[str, str]  # ECU name -> version number

@dataclass
class DownloadProgress:
    ecu_name: str
    version: str
    total_size: int
    downloaded_size: int
    status: str