from typing import Optional
import math
from uds_layer.transfer_enums import EncryptionMethod,CompressionMethod, FlashingECUStatus
from hex_parser.SRecordParser import DataRecord


class FlashingECU:
    Flashing_Request_ID=9000
    def __init__(self,segments:list[DataRecord], recv_DA: int, 
                 encryption_method: EncryptionMethod,
                 compression_method: CompressionMethod,
                 checksum_required: bool):
        self.segments=segments
        self.recv_DA = recv_DA
        self.number_of_segments=len(segments)
        self.current_number_of_segments_send:int=0

        self.encryption_method = encryption_method
        self.compression_method = compression_method
        self.checksum_required = checksum_required
        self.iteration: int = 1
        self.status = FlashingECUStatus.CREATED
        self.ID=FlashingECU.Flashing_Request_ID+1
        FlashingECU.Flashing_Request_ID+=1

