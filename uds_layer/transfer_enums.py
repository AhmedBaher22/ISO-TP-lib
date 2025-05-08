from enum import Enum

class EncryptionMethod(Enum):
    NO_ENCRYPTION = 0x0
    SEC_P_256_R1 = 0x40



class CompressionMethod(Enum):
    NO_COMPRESSION = 0x0
    RLE = 0x1
    HUFFMAN = 0x2
    LZ4 = 0x3

class CheckSumMethod(Enum):
    NO_CHECKSUM = 0x0
    CRC_16 = 0X1
    CRC_32=0X2
    
class TransferStatus(Enum):
    CREATED = "created"
    MEMORY_ERASED="memory erased"
    SENDING_BLOCKS_IN_PROGRESS = "sendingBlocksInProgress"
    COMPLETED = "completed"
    CHECKING_CRC="checking CRC"
    REJECTED = "rejected"
    CLOSED_SUCCESSFULLY = "closedSuccessfully"

class FlashingECUStatus(Enum):
    CREATED = "created"
    SENDING_FIRST_SEGMENT="sending first segment"
    SENDING_CONSECUTIVE_SEGMENTS = "Sending Consecutive segments"
    COMPLETED = "completed sending segments"
    VALIDATING_ENCRYP="seding finalize programming"
    CLOSED_SUCCESSFULLY = "closed Successfully with ensuring checks"
    RESET="RESET"
    REJECTED = "rejected"