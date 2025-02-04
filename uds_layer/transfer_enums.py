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

class TransferStatus(Enum):
    CREATED = "created"
    SENDING_BLOCKS_IN_PROGRESS = "sendingBlocksInProgress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CLOSED_SUCCESSFULLY = "closedSuccessfully"