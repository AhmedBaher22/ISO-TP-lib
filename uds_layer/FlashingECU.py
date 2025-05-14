from typing import Optional
import math
from uds_layer.transfer_enums import EncryptionMethod,CompressionMethod, FlashingECUStatus
from hex_parser.SRecordParser import DataRecord
from typing import Callable

class FlashingECU:
    Flashing_Request_ID=9000
    def __init__(self,segments:list[DataRecord], recv_DA: int, 
                 encryption_method: EncryptionMethod,
                 compression_method: CompressionMethod,
                 checksum_required: bool,
                 successfull_flashing_response:Callable,
                 failed_flashing_response:Callable,
                 flashed_ecu_number:int):
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
        self._flashing_Progress:float=0
        self.successfull_flashing_response:Callable=successfull_flashing_response
        self.failed_flashing_response:Callable=failed_flashing_response
        self.flashed_ecu_number:int=flashed_ecu_number

    def get_req(self)->str:
        msg= f"[FLASH_REQUEST-{self.ID}]-FLASH STAUTS:{self.status.name} "
        return msg
    def add_progress(self,r:float):
        self._flashing_Progress+=r
    def get_progress(self) -> float:
        if self._flashing_Progress > 1:
            return 1
        else:
            return  self._flashing_Progress