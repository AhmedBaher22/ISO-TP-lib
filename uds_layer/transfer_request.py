from typing import Optional
import math
from uds_layer.transfer_enums import EncryptionMethod,CompressionMethod, TransferStatus
from logger import Logger, LogType, ProtocolType
from uds_layer.FlashingECU import FlashingECU, FlashingECUStatus

class TransferRequest:
    def __init__(self, recv_DA: int, data: bytearray, 
                 encryption_method: EncryptionMethod,
                 compression_method: CompressionMethod,
                 memory_address: bytearray,
                 checksum_required: bool,
                 is_multiple_segments:bool=False,
                 flashing_ECU_REQ:FlashingECU=None):
        self.recv_DA = recv_DA
        self.data = data
        self.encryption_method = encryption_method
        self.compression_method = compression_method
        self.memory_address = memory_address
        self.checksum_required = checksum_required
        self.is_multiple_segments=is_multiple_segments
        self.flashing_ECU_REQ:FlashingECU=flashing_ECU_REQ
        self.iteration: int = 1
        
        # Computed or later initialized attributes
        self.data_size = len(data)
        self.max_number_of_block_length: Optional[int] = None
        self.steps_number: Optional[int] = None
        self.current_number_of_steps: int = 0
        self.checksum_value: Optional[int] = None
        self.status = TransferStatus.CREATED
        self.NRC: Optional[int] = None
        self._logger = Logger(ProtocolType.UDS)
        self.compressed_data:bytearray=None

        self.current_trans_ind=0
        self._logger.log_message(
            log_type=LogType.INITIALIZATION,
            message=f"{self.get_req()} NEW Transfer Request has been initialized"
        )
        if self.compression_method != CompressionMethod.NO_COMPRESSION:
            self._logger.log_message(
                log_type=LogType.INITIALIZATION,
                message=f"{self.get_req()}  Transfer Request need compression of type : {self.compression_method.name}"
            )            
            if self.compression_method == CompressionMethod.LZ4:
                self._logger.log_message(
                    log_type=LogType.INITIALIZATION,
                    message=f"{self.get_req()}  compression started procession for Transfer Request"
                )   
                print(self.data)
                self.compressed_data=lz4_compress(bytearray(self.data))
                decopressed=lz4_decompress(self.compressed_data)
                print(decopressed)
                self._logger.log_message(
                    log_type=LogType.INITIALIZATION,
                    message=f"{self.get_req()}  compression finished , here is compressed data: {self.compressed_data}"
                )   

    def calculate_steps_number(self):
        if self.data_size > self.max_number_of_block_length:
            self.steps_number = math.ceil(self.data_size / self.max_number_of_block_length)
        else:
            self.steps_number = 1

    def get_req(self) -> str:
        msg:str
        if self.flashing_ECU_REQ != None:
            msg=f"[FLASH_REQUEST-{self.flashing_ECU_REQ.ID}]-[segment-{self.flashing_ECU_REQ.current_number_of_segments_send}]-[transfer step-{int(self.current_trans_ind/2)}]-FLASH STAUTS:{self.flashing_ECU_REQ.status.name} "
            self.current_trans_ind+=1
        else:
            msg=f"[transfer step-{self.current_trans_ind}]"

        self.current_trans_ind+=1
        return msg