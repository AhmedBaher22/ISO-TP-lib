import logging
import os
from datetime import datetime
from typing import Optional
from exceptions import CANError, CANErrorType

class CANLogger:
    def __init__(self, log_directory="logs"):
        """
        Initialize the logger with specific log categories.
        
        Log Structure:
        logs/
        ├── general/
        │   ├── info.log        (General information logs)
        │   ├── warning.log     (Warning messages)
        │   └── debug.log       (Debug information)
        ├── transactions/
        │   ├── send.log        (Message sending logs)
        │   ├── receive.log     (Message receiving logs)
        │   └── acknowledgment.log (Acknowledgment-related logs)
        ├── errors/
        │   └── error.log       (All error logs)
        └── system/
            ├── initialization.log (Bus initialization logs)
            └── configuration.log  (Configuration-related logs)
        """
        self.log_directory = log_directory
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
        # Create formatters
        standard_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Setup different loggers
        self.loggers = {
            # General loggers
            'info': self._create_logger('info', logging.INFO, 
                                      f"{self.log_directory}/general/info.log"),
            'warning': self._create_logger('warning', logging.WARNING, 
                                         f"{self.log_directory}/general/warning.log"),
            'debug': self._create_logger('debug', logging.DEBUG, 
                                       f"{self.log_directory}/general/debug.log"),
            
            # Transaction loggers
            'send': self._create_logger('send', logging.INFO, 
                                      f"{self.log_directory}/transactions/send.log"),
            'receive': self._create_logger('receive', logging.INFO, 
                                         f"{self.log_directory}/transactions/receive.log"),
            'acknowledgment': self._create_logger('acknowledgment', logging.INFO, 
                                                f"{self.log_directory}/transactions/acknowledgment.log"),
            
            # Error logger
            'error': self._create_logger('error', logging.ERROR, 
                                       f"{self.log_directory}/errors/error.log"),
            
            # System loggers
            'initialization': self._create_logger('initialization', logging.INFO, 
                                                f"{self.log_directory}/system/initialization.log"),
            'configuration': self._create_logger('configuration', logging.INFO, 
                                               f"{self.log_directory}/system/configuration.log")
        }

    def _create_logger(self, name: str, level: int, filename: str) -> logging.Logger:
        """Create a logger with specified configuration"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Remove existing handlers if any
        logger.handlers = []

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Create file handler
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def log_initialization(self, message: str):
        """Log initialization-related messages"""
        self.loggers['initialization'].info(message)
        self.loggers['info'].info(message)

    def log_configuration(self, message: str):
        """Log configuration-related messages"""
        self.loggers['configuration'].info(message)
        self.loggers['info'].info(message)

    def log_send(self, message: str):
        """Log message sending information"""
        self.loggers['send'].info(message)
        self.loggers['info'].info(message)

    def log_receive(self, message: str):
        """Log message receiving information"""
        self.loggers['receive'].info(message)
        self.loggers['info'].info(message)

    def log_acknowledgment(self, message: str):
        """Log acknowledgment-related information"""
        self.loggers['acknowledgment'].info(message)
        self.loggers['info'].info(message)

    def log_error(self, error: CANError):
        """Log error messages"""
        error_details = error.get_error_details()
        error_message = (
            f"Error Type: {error_details['error_type']}\n"
            f"Message: {error_details['message']}\n"
            f"Original Exception: {error_details['original_exception']}\n"
            f"Traceback:\n{error_details['traceback']}"
        )
        self.loggers['error'].error(error_message)

    def log_warning(self, message: str):
        """Log warning messages"""
        self.loggers['warning'].warning(message)
        self.loggers['info'].warning(message)

    def log_info(self, message: str):
        """Log general information"""
        self.loggers['info'].info(message)

    def log_debug(self, message: str):
        """Log debug information"""
        self.loggers['debug'].debug(message)