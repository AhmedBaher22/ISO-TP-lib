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


class Logger:
    def __init__(self, log_directory="iso-tp"):
        """
        Initialize the logger with two log files:
        - success.log: Contains all logs except errors.
        - error.log: Contains only error logs.
        - high_level.log (optional): Contains high-priority logs.
        """
        self.log_directory = os.path.join("..", "logs", log_directory)
        self.success_log = os.path.join(self.log_directory, "success.log")
        self.error_log = os.path.join(self.log_directory, "error.log")
        self.high_level_log = os.path.join("..", "logs", "communication.log")

        self._create_log_structure()
        self._setup_loggers()

    def _create_log_structure(self):
        """Create the log directory structure"""
        os.makedirs(self.log_directory, exist_ok=True)

    def _setup_loggers(self):
        """Setup loggers for success, error, and high-level logs"""
        self.success_logger = self._create_logger("success", logging.INFO, self.success_log)
        self.error_logger = self._create_logger("error", logging.ERROR, self.error_log)
        self.high_level_logger = self._create_logger("communication", logging.INFO, self.high_level_log)

    def _create_logger(self, name: str, level: int, filename: str) -> logging.Logger:
        """Create and configure a logger"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.handlers = []  # Remove existing handlers

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

        # File handler
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def log_message(self, log_type: LogType, message: str, important: bool = False):
        """Log a message based on log type, and optionally add to high-level log."""
        log_level = self._get_log_level(log_type)
        formatted_message = f"{log_type.value.upper()} - {message}."  # Include LogType after timestamp

        if log_type == LogType.ERROR:
            self.error_logger.log(log_level, formatted_message)
        else:
            self.success_logger.log(log_level, formatted_message)

        if important:
            self.high_level_logger.log(logging.INFO, formatted_message)

    def _get_log_level(self, log_type: LogType) -> int:
        """Map LogType to logging level."""
        return {
            LogType.INFO: logging.INFO,
            LogType.WARNING: logging.WARNING,
            LogType.DEBUG: logging.DEBUG,
            LogType.SEND: logging.INFO,
            LogType.RECEIVE: logging.INFO,
            LogType.ACKNOWLEDGMENT: logging.INFO,
            LogType.ERROR: logging.ERROR,
            LogType.INITIALIZATION: logging.INFO,
            LogType.CONFIGURATION: logging.INFO
        }[log_type]
