from typing import Optional
import math
from uds_layer.transfer_enums import EncryptionMethod,CompressionMethod, TransferStatus

class TransferRequest:
    def __init__(self, recv_DA: int, data: bytearray, 
                 encryption_method: EncryptionMethod,
                 compression_method: CompressionMethod,
                 memory_address: bytearray,
                 checksum_required: bool):
        self.recv_DA = recv_DA
        self.data = data
        self.encryption_method = encryption_method
        self.compression_method = compression_method
        self.memory_address = memory_address
        self.checksum_required = checksum_required
        self.iteration: int = 1
        # Computed or later initialized attributes
        self.data_size = len(data)
        self.max_number_of_block_length: Optional[int] = None
        self.steps_number: Optional[int] = None
        self.current_number_of_steps: int = 0
        self.checksum_value: Optional[int] = None
        self.status = TransferStatus.CREATED
        self.NRC: Optional[int] = None

    def calculate_steps_number(self):
        if self.data_size > self.max_number_of_block_length:
            self.steps_number = math.ceil(self.data_size / self.max_number_of_block_length)
        else:
            self.steps_number = 1