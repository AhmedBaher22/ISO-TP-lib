from typing import Optional
from AddressingMode import AddressingMode


class Address:
    def __init__(self, addressing_mode: AddressingMode.Normal_11bits = 0, txid: Optional[int] = None, rxid: Optional[int] = None):
        """
        Initializes the Address object with addressing mode, transmit ID, and receive ID.
        
        :param addressing_mode: The type of CAN ID (11-bit or 29-bit).
        :param txid: Optional transmit ID.
        :param rxid: Optional receive ID.
        """
        self.addressing_mode = addressing_mode
        self._txid = txid
        self._rxid = rxid

    def __repr__(self):
        return (f"Address(addressing_mode={self.addressing_mode}, "
                f"txid={self._txid}, rxid={self._rxid})")
