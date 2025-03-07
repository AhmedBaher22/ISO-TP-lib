from enum import Enum

class EncryptionMethod(Enum):
    NO_ENCRYPTION = 0x0
    AES_128 = 0x1
    AES_256 = 0x2
    RSA_2048 = 0x3

class CompressionMethod(Enum):
    NO_COMPRESSION = 0x0
    RLE = 0x1
    HUFFMAN = 0x2
    LZ77 = 0x3

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
    COMPLETED = "completed"
    CLOSED_SUCCESSFULLY = "closed Successfully with ensuring checks"
    RESET="RESET"
    REJECTED = "rejected"