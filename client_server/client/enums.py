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

class ClientStatus(Enum):
    OFFLINE = "offline"
    AUTHENTICATED="Authenticated"
    CHECK_FOR_UPDATES = "checkForUpdates"
    WAITING_FOR_RESPONSE = "waitingForResponse"
    VERSIONS_UP_TO_DATE = "versionsUpToDate"
    WAITING_FLASHING_SOME_ECUS="waiting flashing some ecus"
    DOWNLOAD_NEEDED = "downloadNeeded"
    REQUESTING_DOWNLOAD = "requestingDownload"
    DOWNLOAD_IN_PROGRESS = "downloadInProgress"
    CONNECTION_TIMEOUT = "connectionTimeout"
    DOWNLOAD_COMPLETED = "downloadCompleted"


class ClientDownloadStatus(Enum):
    INITIALIZING = "initializing"
    REQUESTING = "requesting"
    DOWNLOADING = "downloading"
    IN_FLASHING="IN FLASHING"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partiallyCompleted"
    DOWNLOAD_COMPLETED = "downloadCompleted"
