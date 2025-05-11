"""
Enums for the ECU Update System.
"""

from enum import Enum, auto

class ClientStatus(Enum):
    """Status of the client"""
    OFFLINE = auto()
    AUTHENTICATED = auto()
    CHECK_FOR_UPDATES = auto()
    WAITING_FOR_RESPONSE = auto()
    VERSIONS_UP_TO_DATE = auto()
    DOWNLOAD_NEEDED = auto()
    REQUESTING_DOWNLOAD = auto()
    DOWNLOAD_IN_PROGRESS = auto()
    DOWNLOAD_COMPLETED = auto()
    WAITING_FLASHING_SOME_ECUS = auto()

class ClientDownloadStatus(Enum):
    """Status of a download request"""
    INITIALIZING = auto()
    REQUESTING = auto()
    DOWNLOADING = auto()
    DOWNLOAD_COMPLETED = auto() 
    IN_FLASHING = auto()
    COMPLETED = auto()
    FAILED = auto()

class ServiceType(Enum):
    """Service types for ECU updates"""
    CHECK_FOR_UPDATE = "CHECK_FOR_UPDATE"
    DOWNLOAD_UPDATE = "DOWNLOAD_UPDATE"
    INSTALL_UPDATE = "INSTALL_UPDATE"

class DownloadStatus(Enum):
    """Status of a download"""
    INITIALIZING = "INITIALIZING"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED_SUCCESSFULLY = "FINISHED_SUCCESSFULLY"
    FAILED = "FAILED"