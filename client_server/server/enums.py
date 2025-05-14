from enum import Enum

class ServiceType(Enum):
    CHECK_FOR_UPDATE = "checkingForUpdate"
    DOWNLOAD_UPDATE = "downloadingNewUpdate"

class RequestStatus(Enum):
    CHECKING_AUTHENTICITY = "checkingAuthenticity"
    AUTHENTICATED = "authenticated"
    NON_AUTHENTICATED = "nonAuthenticated"
    SERVICE_IN_PROGRESS = "serviceInProgress"
    FINISHED_SUCCESSFULLY = "finishedSuccessfully"
    FAILED = "failed"
    REJECTED = "rejected"

class DownloadStatus(Enum):
    PREPARING_FILES = "preparingFiles"
    SENDING_IN_PROGRESS = "sendingInProgress"
    FINISHED_SUCCESSFULLY = "finishedSuccessfully"
    FAILED_PARTIAL_SUCCESS = "failedWithSomeFilesSendSuccessfully"
    ALL_FAILED = "allFailed"