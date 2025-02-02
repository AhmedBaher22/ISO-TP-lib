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
        Initialize the logger with specific log categories.

        Adds a new high-level log file that captures critical logs for user visibility.
        """
        self.log_directory = "..\\logs\\" + log_directory
        self.high_level_log = "..\\logs\\communication"
        self._create_log_structure()
        self._setup_loggers()

    def _create_log_structure(self):
        """Create the log directory structure"""
        directories = [
            "general",
            "transactions",
            "errors",
            "system"
        ]

        for directory in directories:
            os.makedirs(f"{self.log_directory}/{directory}", exist_ok=True)

    def _setup_loggers(self):
        """Setup different loggers for different types of logs"""
        self.loggers = {
            LogType.INFO: self._create_logger('info', logging.INFO, f"{self.log_directory}/general/info.log"),
            LogType.WARNING: self._create_logger('warning', logging.WARNING, f"{self.log_directory}/general/warning.log"),
            LogType.DEBUG: self._create_logger('debug', logging.DEBUG, f"{self.log_directory}/general/debug.log"),
            LogType.SEND: self._create_logger('send', logging.INFO, f"{self.log_directory}/transactions/send.log"),
            LogType.RECEIVE: self._create_logger('receive', logging.INFO, f"{self.log_directory}/transactions/receive.log"),
            LogType.ACKNOWLEDGMENT: self._create_logger('acknowledgment', logging.INFO, f"{self.log_directory}/transactions/acknowledgment.log"),
            LogType.ERROR: self._create_logger('error', logging.ERROR, f"{self.log_directory}/errors/error.log"),
            LogType.INITIALIZATION: self._create_logger('initialization', logging.INFO, f"{self.log_directory}/system/initialization.log"),
            LogType.CONFIGURATION: self._create_logger('configuration', logging.INFO, f"{self.log_directory}/system/configuration.log"),
        }

        # Create high-level logger
        self.high_level_logger = self._create_logger('communication', logging.INFO, self.high_level_log)


    def _create_logger(self, name: str, level: int, filename: str) -> logging.Logger:
        """Create a logger with specified configuration"""
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

    def log_message(self, log_type: LogType, message: str, high_level: bool = False):
        """Log a message to the appropriate log file and optionally to the high-level log."""
        if log_type in self.loggers:
            self.loggers[log_type].log(self._get_log_level(log_type), message)

            if high_level:
                self.high_level_logger.log(logging.INFO, f"{log_type.value.upper()}: {message}")


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
