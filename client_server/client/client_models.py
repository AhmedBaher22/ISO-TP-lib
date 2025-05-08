
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enums import ClientStatus, ClientDownloadStatus
from shared_models import ECUVersion, CarInfo
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from hex_parser.SRecordParser import DataRecord

@dataclass
class flashingEcu:
    ecu_number:int #the number of ecu index downloaded in the download request
    ecu_name:str
    old_version:str
    new_version:str
    old_version_path:str
    new_version_path:str
    delta_records: DataRecord
    flashing_done: bool
    roll_back_delta:DataRecord
    old_version_data_records:DataRecord
    flashing_retries:int = 0
    roll_back_needed:bool= False
    roll_back_done:bool=False
    def __init__(self, ecu_number: int,ecu_name:str,old_version:str,new_version:str, old_version_path: str, new_version_path: str,
                 delta_records: DataRecord, flashing_done: bool,roll_back_delta: DataRecord,old_version_data_records:DataRecord,
                 flashing_retries: int = 0, roll_back_needed: bool = False,roll_back_done:bool=False ):
        self.ecu_number = ecu_number
        self.ecu_name=ecu_name
        self.old_version=old_version
        self.new_version=new_version
        self.old_version_path = old_version_path
        self.new_version_path = new_version_path
        self.delta_records = delta_records
        self.flashing_done = flashing_done
        self.flashing_retries = flashing_retries
        self.roll_back_needed = roll_back_needed
        self.roll_back_done=roll_back_done
        self.roll_back_delta=roll_back_delta
        self.old_version_data_records=old_version_data_records
@dataclass
class ClientDownloadRequest:
    request_id: str
    timestamp: datetime
    car_info: CarInfo
    required_updates: Dict[str, str]
    status: ClientDownloadStatus
    total_ecus: int
    flashed_ecus:List[flashingEcu]=field(default_factory=list)
    completed_ecus: int = 0
    downloaded_versions: Dict[str, str] = field(default_factory=dict)
    total_size: int = 0
    downloaded_size: int = 0
    file_offsets: Dict[str, int] = field(default_factory=dict)  # Track offset for each ECU
    flashed_order_index:int=0
    number_of_flashed_ecus:int=0


    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat(),
            'car_info': {
                'car_type': self.car_info.car_type,
                'car_name': self.car_info.car_name,
                'car_model': self.car_info.car_model,
                'car_id': self.car_info.car_id,
                'ecu_versions': self.car_info.ecu_versions
            },
            'required_updates': self.required_updates,
            'status': self.status.value,
            'total_ecus': self.total_ecus,
            'completed_ecus': self.completed_ecus,
            'downloaded_versions': self.downloaded_versions,
            'total_size': self.total_size,
            'downloaded_size': self.downloaded_size,
            'file_offsets': self.file_offsets,
            'flashed_ecus': [
                {
                    'ecu_number': ecu.ecu_number,
                    'ecu_name': ecu.ecu_name,
                    'old_version': ecu.old_version,
                    'new_version': ecu.new_version,
                    'old_version_path': ecu.old_version_path,
                    'new_version_path': ecu.new_version_path,
                    'delta_records': [record.to_dict() for record in ecu.delta_records],
                    'flashing_done': ecu.flashing_done,
                    'flashing_retries': ecu.flashing_retries,
                    'roll_back_needed': ecu.roll_back_needed,
                    'roll_back_done' : ecu.roll_back_done,
                    'roll_back_delta' : ecu.roll_back_delta,
                    'old_version_data_records': ecu.old_version_data_records

                } for ecu in self.flashed_ecus
            ],
            'flashed_order_index': self.flashed_order_index,
            'number_of_flashed_ecus': self.number_of_flashed_ecus
        }


    @classmethod
    def from_dict(cls, data: dict) -> 'ClientDownloadRequest':
        """Create instance from dictionary"""
        flashed_ecus = [
            flashingEcu(
                ecu_number=ecu_data['ecu_number'],
                ecu_name=ecu_data['ecu_name'],
                old_version=ecu_data['old_version'],
                new_version=ecu_data['new_version'],
                old_version_path=ecu_data['old_version_path'],
                new_version_path=ecu_data['new_version_path'],
                delta_records=DataRecord.from_dict(ecu_data['delta_records']),
                flashing_done=ecu_data['flashing_done'],
                flashing_retries=ecu_data.get('flashing_retries', 0),
                roll_back_needed=ecu_data.get('roll_back_needed', False),
                roll_back_done=ecu_data.get('roll_back_done', False),
                roll_back_delta=DataRecord.from_dict(ecu_data['roll_back_delta']),
                old_version_data_records=DataRecord.from_dict(ecu_data['old_version_data_records'])
            ) for ecu_data in data.get('flashed_ecus', [])
        ]

        return cls(
            request_id=data['request_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            car_info=CarInfo(**data['car_info']),
            required_updates=data['required_updates'],
            status=ClientDownloadStatus(data['status']),
            total_ecus=data['total_ecus'],
            completed_ecus=data['completed_ecus'],
            downloaded_versions=data['downloaded_versions'],
            total_size=data['total_size'],
            downloaded_size=data['downloaded_size'],
            file_offsets=data.get('file_offsets', {}),
            flashed_ecus=flashed_ecus,
            flashed_order_index=data.get('flashed_order_index', 0),
            number_of_flashed_ecus=data.get('number_of_flashed_ecus', 0)
        )

