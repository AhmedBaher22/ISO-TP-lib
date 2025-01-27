class IsoTpException(Exception):
    """Base class for all ISO-TP related exceptions."""
    pass


class InvalidFirstFrameException(IsoTpException):
    """Raised when an invalid first frame is received."""

    def __init__(self, frame_type):
        super().__init__(f"The first frame can't be {frame_type}")


class ConsecutiveFrameOutOfSequenceException(IsoTpException):
    """Raised when a consecutive frame is received out of sequence."""

    def __init__(self, expected_seq, received_seq):
        super().__init__(
            f"Consecutive message out of sequence! Expected sequence number {expected_seq} and received {received_seq}")


class UnexpectedFrameTypeException(IsoTpException):
    """Raised when an unexpected frame type is received."""

    def __init__(self, expected_type, received_type):
        super().__init__(f"Was expecting {expected_type} and received {received_type}")


class ConsecutiveFrameBeforeFlowControlException(IsoTpException):
    """Raised when a consecutive frame is received before sending the control flow."""

    def __init__(self):
        super().__init__("Received ConsecutiveFrame before sending the control flow")


class MessageSizeExceededException(IsoTpException):
    """Raised when the received message is larger than expected."""

    def __init__(self, expected_size, received_size):
        super().__init__(
            f"Message received larger than expected! Expected size is {expected_size}, received {received_size}")


class MessageLengthExceededException(IsoTpException):
    """Raised when the message length exceeds the ISO-TP limit."""
    def __init__(self):
        super().__init__("Message length exceeds the maximum limit of 4095 bytes for ISO-TP.")


class FlowStatusAbortException(IsoTpException):
    """Raised when a flow status 'Abort' is received, terminating the transmission."""
    def __init__(self):
        super().__init__("Flow status: Abort received. Transmission terminated.")


class InvalidFlowStatusException(IsoTpException):
    """Raised when an invalid flow status is received."""
    def __init__(self, flow_status_value):
        super().__init__(f"Invalid flow status received: {flow_status_value}")


class TimeoutException(IsoTpException):
    """Raised when the message length exceeds the ISO-TP limit."""
    def __init__(self):
        super().__init__("Timeout Elapsed!")
