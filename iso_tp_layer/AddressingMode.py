from enum import Enum


class AddressingMode(Enum):
    Normal_11bits = 0  # Standard 11-bit CAN identifier
    Extended_29bits = 1  # Extended 29-bit CAN identifier

