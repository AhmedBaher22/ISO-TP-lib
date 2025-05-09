from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enums import *

@dataclass
class Version:
    version_number: str
    compatible_car_types: List[str]
    hex_file_path: str

@dataclass
class ECU:
    name: str
    model_number: str
    versions: List[Version]
    
    def get_latest_version(self) -> Version:
        # Assuming versions are stored in order, latest being last
        print(f"latest version {self.versions[-1] if self.versions else None}")
        return self.versions[-1] if self.versions else None

@dataclass
class CarType:
    name: str
    model_number: str
    ecus: List[ECU]
    manufactured_count: int
    car_ids: List[str]
    
    def check_for_updates(self, current_versions: Dict[str, str]) -> Dict[str, str]:
        print("Entered check_for_updates")
        """
        Check if car needs updates by comparing current versions with latest versions
        Returns dict of ECU names and their required update versions
        """
        updates_needed = {}
        
        for ecu in self.ecus:
            print(f"\n\n current_versions: ")
            print(current_versions.values)

            current_versions = {key.lower(): value.lower() for key, value in current_versions.items()}

            print(current_versions)
            if ecu.name in current_versions:
                latest_version = ecu.get_latest_version()
                if latest_version and current_versions[ecu.name] != latest_version.version_number:
                    print(f"latest_version.version_number: {latest_version.version_number}")
                    updates_needed[ecu.name] = latest_version.version_number
        return updates_needed

@dataclass
class Request:
    timestamp: datetime
    car_type: str
    car_id: str
    ip_address: str
    port: int
    service_type: ServiceType
    metadata: Dict  # Contains ECU versions
    status: RequestStatus

@dataclass
class DownloadRequest:
    timestamp: datetime
    car_type: str
    car_id: str
    ip_address: str
    port: int
    required_versions: Dict[str, str]  # ECU name -> version number
    old_versions: Dict[str, str]  # ECU name -> version number
    status: DownloadStatus
    total_size: int = 0
    transferred_size: int = 0
    active_transfers: Dict[str, bool] = None
    file_offsets: Dict[str, int] = field(default_factory=dict)
