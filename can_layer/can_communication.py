import can
from typing import Callable, List, Dict, Optional
import time
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from can_layer.enums import CANInterface
from can_layer.logger import CANLogger
from can_layer.CanExceptions import (
    CANError,
    CANInitializationError,
    CANFilterError,
    CANTransmissionError,
    CANReceptionError,
    CANTimeoutError,
    CANAcknowledgmentError,
    CANConfigurationError,
    CANShutdownError
)


class CANConfiguration:
    """Configuration class for CAN communication parameters."""

    def __init__(self,
                 recv_callback: Callable,
                 interface: CANInterface = CANInterface.VECTOR,
                 channel: int = 0,
                 app_name: str = "CANApp",
                 fd_flag: bool = False,
                 extended_flag: bool = False,
                 bitrate: int = 500000):
        """
        Initialize CAN configuration.
        
        Args:
            interface: CAN interface type (e.g., Vector, SocketCAN)
            channel: CAN channel number
            app_name: Application name for the CAN session
            fd_flag: Flag for CAN FD support
            extended_flag: Flag for extended CAN ID support
            bitrate: CAN bus bitrate
        """
        self.interface = interface
        self.channel = channel
        self.app_name = app_name
        self.fd_flag = fd_flag
        self.extended_flag = extended_flag
        self.bitrate = bitrate
        self.recv_callback = recv_callback

    def validate(self):
        """Validate configuration parameters."""
        if not isinstance(self.channel, int) or self.channel < 0:
            raise CANConfigurationError("Invalid channel number")
        if not isinstance(self.bitrate, int) or self.bitrate <= 0:
            raise CANConfigurationError("Invalid bitrate")
        if not isinstance(self.app_name, str) or not self.app_name:
            raise CANConfigurationError("Invalid application name")


class CANCommunication:
    """Main class for CAN communication handling."""

    def __init__(self, config: CANConfiguration):
        """
        Initialize CAN communication.
        
        Args:
            config: CANConfiguration object containing setup parameters
        """
        self.config = config
        self.logger = CANLogger()
        self.bus = None
        self._initialize_bus()

    def _initialize_bus(self):
        """Initialize the CAN bus with the provided configuration."""
        try:
            # Validate configuration before initialization
            self.config.validate()

            self.bus = can.Bus(
                interface=self.config.interface.value,
                channel=self.config.channel,
                app_name=self.config.app_name,
                fd=self.config.fd_flag,
                bitrate=self.config.bitrate
            )
            self.logger.log_initialization("CAN bus initialized successfully")

        except CANConfigurationError as e:
            self.logger.log_error(e)
            raise

        except Exception as e:
            error = CANInitializationError(
                message="Failed to initialize CAN bus",
                original_exception=e
            )
            self.logger.log_error(error)
            raise error

    def set_filters(self, filters: List[Dict]):
        """
        Set message filters for the CAN bus.
        
        Args:
            filters: List of filter dictionaries
        """
        try:
            if not self.bus:
                raise CANError("CAN bus not initialized")

            self.bus.set_filters(filters)
            self.logger.log_configuration(f"Filters set successfully: {filters}")

        except Exception as e:
            error = CANFilterError(
                message="Failed to set CAN filters",
                original_exception=e
            )
            self.logger.log_error(error)
            raise error

    def send_message(self,
                     arbitration_id: int,
                     data: bytearray,
                     timeout: float = 1.0,
                     require_ack: bool = False,
                     retries: int = 3,
                     retry_delay: float = 0.5) -> bool:
        """
        Send a CAN message with optional acknowledgment waiting.
        
        Args:
            arbitration_id: CAN message ID
            data: Message data bytes
            timeout: Timeout for acknowledgment waiting
            require_ack: Whether to wait for acknowledgment
            retries: Number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.bus:
            raise CANError("CAN bus not initialized")

        message = can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=self.config.extended_flag,
            is_fd=self.config.fd_flag
        )

        attempts_remaining = retries
        while attempts_remaining > 0:
            try:
                # Send the message
                self.bus.send(message)
                self.logger.log_send(
                    f"Message sent: ID=0x{arbitration_id:X}, Data={data}, "
                    f"Attempts remaining: {attempts_remaining}"
                )

                if require_ack:
                    # Wait for acknowledgment
                    ack = self.receive_message(timeout=timeout)
                    if ack:
                        self.logger.log_acknowledgment(
                            f"Acknowledgment received for ID=0x{arbitration_id:X}"
                        )
                        return True
                    else:
                        attempts_remaining -= 1
                        if attempts_remaining > 0:
                            self.logger.log_warning(
                                f"No acknowledgment received. Retrying... "
                                f"{attempts_remaining} attempts left"
                            )
                            time.sleep(retry_delay)
                        continue
                else:
                    return True

            except Exception as e:
                attempts_remaining -= 1
                error = CANTransmissionError(
                    message=f"Failed to send message (attempts left: {attempts_remaining})",
                    original_exception=e
                )
                self.logger.log_error(error)

                if attempts_remaining > 0:
                    time.sleep(retry_delay)
                continue

        error = CANAcknowledgmentError(
            message=f"Failed to send message 0x{arbitration_id:X} after all retries"
        )
        self.logger.log_error(error)
        return False

    def receive_message(self, timeout: float = 1.0) -> Optional[can.Message]:
        """
        Receive a CAN message.
        
        Args:
            timeout: Maximum time to wait for message
            
        Returns:
            Optional[can.Message]: Received message or None if timeout
        """
        if not self.bus:
            raise CANError("CAN bus not initialized")

        try:
            message = self.bus.recv(timeout=timeout)

            if message:
                self.logger.log_receive(
                    f"Message received: ID=0x{message.arbitration_id:X}, "
                    f"Data={message.data}"
                )
                print("/n/n")
                print("esammmmmm", message)

                self.config.recv_callback(message)

            self.logger.log_warning(
                f"No message received within timeout period ({timeout}s)"
            )
            return None

        except Exception as e:
            error = CANReceptionError(
                message="Error receiving message",
                original_exception=e
            )
            self.logger.log_error(error)
            raise error

    def close(self):
        """Close the CAN bus connection."""
        try:
            if self.bus:
                self.bus.shutdown()
                self.logger.log_initialization("CAN bus shut down successfully")
                self.bus = None

        except Exception as e:
            error = CANShutdownError(
                message="Error shutting down CAN bus",
                original_exception=e
            )
            self.logger.log_error(error)
            raise error

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    @property
    def is_connected(self) -> bool:
        """Check if CAN bus is connected and initialized."""
        return self.bus is not None

    def reset(self):
        """Reset the CAN bus connection."""
        self.logger.log_initialization("Resetting CAN bus connection")
        self.close()
        self._initialize_bus()

    def flush_receive_buffer(self):
        """Flush the receive buffer by reading all pending messages."""
        try:
            self.logger.log_info("Flushing receive buffer")
            while self.receive_message(timeout=0.1):
                pass
            self.logger.log_info("Receive buffer flushed successfully")
        except Exception as e:
            error = CANError(
                message="Error flushing receive buffer",
                original_exception=e
            )
            self.logger.log_error(error)
            raise error

    def get_bus_statistics(self) -> Dict:
        """Get current bus statistics."""
        try:
            if not self.bus:
                raise CANError("CAN bus not initialized")

            stats = {
                "messages_sent": getattr(self.bus, "messages_sent", 0),
                "messages_received": getattr(self.bus, "messages_received", 0),
                "errors": getattr(self.bus, "errors", 0),
                "state": getattr(self.bus, "state", "unknown")
            }

            self.logger.log_info(f"Bus statistics retrieved: {stats}")
            return stats

        except Exception as e:
            error = CANError(
                message="Error getting bus statistics",
                original_exception=e
            )
            self.logger.log_error(error)
            raise error

    def clear_bus_statistics(self):
        """Clear bus statistics counters."""
        try:
            if not self.bus:
                raise CANError("CAN bus not initialized")

            if hasattr(self.bus, "clear_statistics"):
                self.bus.clear_statistics()
                self.logger.log_info("Bus statistics cleared successfully")
            else:
                self.logger.log_warning("Bus statistics clearing not supported")

        except Exception as e:
            error = CANError(
                message="Error clearing bus statistics",
                original_exception=e
            )
            self.logger.log_error(error)
            raise error
