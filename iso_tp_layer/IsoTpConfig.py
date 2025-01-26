from typing import Callable
from Address import Address


class IsoTpConfig:
    """
    A configuration class (struct-like) for ISO-TP settings.
    """
    def __init__(self, max_block_size, timeout, stmin, on_recv_success: Callable, on_recv_error: Callable):
        if stmin > timeout:
            raise ValueError("stmin must be less than or equal to timeout.")
        # self.address = address
        self.max_block_size = max_block_size
        self.timeout = timeout
        self.stmin = stmin
        self.on_recv_success = on_recv_success
        self.on_recv_error = on_recv_error

