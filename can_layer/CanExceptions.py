from enum import Enum, auto
from typing import Optional
import traceback


class CANErrorType(Enum):
    """Enum for different types of CAN errors"""
    INITIALIZATION = auto()
    FILTER = auto()
    TRANSMISSION = auto()
    RECEPTION = auto()
    TIMEOUT = auto()
    ACKNOWLEDGMENT = auto()
    CONFIGURATION = auto()
    SHUTDOWN = auto()
    GENERAL = auto()


class CANError(Exception):
    """Base exception class for CAN-related errors."""

    def __init__(self,
                 message: str,
                 error_type: CANErrorType = CANErrorType.GENERAL,
                 original_exception: Optional[Exception] = None):
        self.message = message
        self.error_type = error_type
        self.original_exception = original_exception
        self.traceback = traceback.format_exc()
        super().__init__(self.message)

    def get_error_details(self) -> dict:
        """Return detailed error information"""
        return {
            "error_type": self.error_type.name,
            "message": self.message,
            "original_exception": str(self.original_exception) if self.original_exception else None,
            "traceback": self.traceback
        }


class CANInitializationError(CANError):
    """Raised when CAN bus initialization fails."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_type=CANErrorType.INITIALIZATION,
            original_exception=original_exception
        )


class CANFilterError(CANError):
    """Raised when setting CAN filters fails."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_type=CANErrorType.FILTER,
            original_exception=original_exception
        )


class CANTransmissionError(CANError):
    """Raised when sending a CAN message fails."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_type=CANErrorType.TRANSMISSION,
            original_exception=original_exception
        )


class CANReceptionError(CANError):
    """Raised when receiving a CAN message fails."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_type=CANErrorType.RECEPTION,
            original_exception=original_exception
        )


class CANTimeoutError(CANError):
    """Raised when a CAN operation times out."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_type=CANErrorType.TIMEOUT,
            original_exception=original_exception
        )


class CANAcknowledgmentError(CANError):
    """Raised when no acknowledgment is received."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_type=CANErrorType.ACKNOWLEDGMENT,
            original_exception=original_exception
        )


class CANConfigurationError(CANError):
    """Raised when there's an error in CAN configuration."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_type=CANErrorType.CONFIGURATION,
            original_exception=original_exception
        )


class CANShutdownError(CANError):
    """Raised when there's an error during CAN shutdown."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_type=CANErrorType.SHUTDOWN,
            original_exception=original_exception
        )


def handle_can_exception(exception: Exception) -> CANError:
    """Convert various exceptions to appropriate CAN exceptions."""
    if isinstance(exception, can.interfaces.vector.exceptions.VectorInitializationError):
        return CANInitializationError(
            message="Vector hardware initialization failed",
            original_exception=exception
        )
    elif isinstance(exception, ValueError):
        return CANConfigurationError(
            message="Invalid CAN configuration",
            original_exception=exception
        )
    elif isinstance(exception, OSError):
        return CANInitializationError(
            message="Hardware or system error",
            original_exception=exception
        )
    elif isinstance(exception, can.CanError):
        return CANError(
            message="General CAN error",
            error_type=CANErrorType.GENERAL,
            original_exception=exception
        )
    else:
        return CANError(
            message="Unexpected error",
            error_type=CANErrorType.GENERAL,
            original_exception=exception
        )
