from typing import Callable
import sys
import os
# Add the package root directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.Address import Address


class IsoTpConfig:
    """
    A configuration class (struct-like) for ISO-TP settings.
    """
    def __init__(self, max_block_size, timeout, stmin,
                  on_recv_success: Callable, on_recv_error: Callable,
                  recv_id: int):
        if stmin > timeout:
            raise ValueError("stmin must be less than or equal to timeout.")
        # self.address = address
        self.max_block_size = max_block_size
        self.timeout = timeout
        self.stmin = stmin
        self.on_recv_success = on_recv_success
        self.on_recv_error = on_recv_error
        self.send_fn: Callable = None
        self.recv_id = recv_id

