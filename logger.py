import logging
import os
from enum import Enum


class LogType(Enum):
    INFO = "info"
    WARNING = "warning"
    DEBUG = "debug"
    SEND = "send"
    RECEIVE = "receive"
    ACKNOWLEDGMENT = "acknowledgment"
    ERROR = "error"
    INITIALIZATION = "initialization"
    CONFIGURATION = "configuration"


class ProtocolType(Enum):
    ISO_TP = "ISO-TP"
    UDS = "UDS"
    CAN = "CAN"


class Logger:
    def __init__(self, protocol: ProtocolType):
        """
        Initialize a logger with a separate directory and log files for the chosen protocol.

        Args:
            protocol (ProtocolType): The selected protocol (ISO-TP, UDS, CAN).
        """
        self.protocol = protocol.value  # Store protocol name as a string

        # Define log directory based on protocol
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_directory = os.path.join(current_dir, "logs", self.protocol)
        self.success_log = os.path.join(self.log_directory, "success.log")
        self.error_log = os.path.join(self.log_directory, "error.log")
        self.communication_log = os.path.join(current_dir, "logs", "general_logs.log")

        # **Ensure the log directory exists before creating loggers**
        self._create_log_structure()

        # Create separate loggers for each protocol instance
        self.success_logger = self._create_logger(f"{self.protocol}_success", self.success_log, logging.INFO, False)
        self.error_logger = self._create_logger(f"{self.protocol}_error", self.error_log, logging.ERROR, False)
        self.communication_logger = self._create_logger(f"{self.protocol}_communication", self.communication_log, logging.INFO, True)

    def _create_log_structure(self):
        """Create the log directory structure for the protocol."""
        os.makedirs(self.log_directory, exist_ok=True)


    def _create_logger(self, name: str, filename: str, level: int, add_console: bool) -> logging.Logger:
        """Create a unique logger for each protocol instance."""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Remove existing handlers if re-initialized
        if logger.hasHandlers():
            logger.handlers.clear()

        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

        # File handler (this now works since directory exists)
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler (only for communication log)
        if add_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    def log_message(self, log_type: LogType, message: str):
        """
        Logs a message in the format:
        YYYY-MM-DD HH:MM:SS - PROTOCOL - LOG_TYPE - message

        Args:
            log_type (LogType): Type of log message.
            message (str): The actual log message.
        """
        formatted_message = f"{self.protocol} - {log_type.name} - {message}"

        # Log to respective log files
        if log_type == LogType.ERROR:
            self.error_logger.error(formatted_message)
        else:
            self.success_logger.info(formatted_message)

        # Always log to communication.log and print once
        self.communication_logger.info(formatted_message)
