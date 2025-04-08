from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enums import ClientStatus, ClientDownloadStatus
from shared_models import ECUVersion, CarInfo

@dataclass
class ClientDownloadRequest:
    request_id: str
    timestamp: datetime
    car_info: CarInfo
    required_updates: Dict[str, str]  # ECU name -> version number
    status: ClientDownloadStatus
    total_ecus: int
    completed_ecus: int = 0
    downloaded_versions: Dict[str, str] = field(default_factory=dict)  # ECU name -> version
    total_size: int = 0
    downloaded_size: int = 0
    retry_count: int = 0
    last_successful_download: Optional[datetime] = None
    
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
            'retry_count': self.retry_count,
            'last_successful_download': self.last_successful_download.isoformat() 
                if self.last_successful_download else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ClientDownloadRequest':
        """Create instance from dictionary"""
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
            retry_count=data['retry_count'],
            last_successful_download=datetime.fromisoformat(data['last_successful_download'])
                if data['last_successful_download'] else None
        )