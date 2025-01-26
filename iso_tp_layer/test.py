from typing import Union
from bitarray import bitarray
from typing import Callable, List, Union
from bitarray import bitarray
from Address import Address
from iso_tp_layer.IsoTpConfig import IsoTpConfig
from iso_tp_layer.frames.ConsecutiveFrameMessage import ConsecutiveFrameMessage
from iso_tp_layer.frames.ErrorFrameMessage import ErrorFrameMessage
from iso_tp_layer.frames.FirstFrameMessage import FirstFrameMessage
from iso_tp_layer.frames.FlowControlFrameMessage import FlowControlFrameMessage
from iso_tp_layer.frames.FlowStatus import FlowStatus
from iso_tp_layer.frames.FrameMessage import FrameMessage
from iso_tp_layer.frames.FrameType import FrameType
from iso_tp_layer.frames.SingleFrameMessage import SingleFrameMessage

from bitarray import bitarray
import numpy as np


def message_to_bitarray(message: FrameMessage) -> bitarray:
    bits = bitarray()

    if isinstance(message, SingleFrameMessage):
        print(message.dataLength)
        pci_byte = (FrameType.SingleFrame.value << 4) | message.dataLength
        bits.frombytes(bytes([pci_byte]))  # PCI byte
        bits.extend(message.data)  # Data bits

    elif isinstance(message, FirstFrameMessage):
        pci_byte1 = (FrameType.FirstFrame.value << 4) | ((message.dataLength >> 8) & 0xF)
        pci_byte2 = message.dataLength & 0xFF
        bits.frombytes(bytes([pci_byte1, pci_byte2]))  # PCI bytes
        bits.extend(message.data)  # Data bits

    elif isinstance(message, ConsecutiveFrameMessage):
        pci_byte = (FrameType.ConsecutiveFrame.value << 4) | message.sequenceNumber
        bits.frombytes(bytes([pci_byte]))  # PCI byte
        bits.extend(message.data)  # Data bits

    elif isinstance(message, FlowControlFrameMessage):
        pci_byte = (FrameType.FlowControlFrame.value << 4) | message.flowStatus.value
        bits.frombytes(bytes([pci_byte, message.blockSize, message.separationTime]))  # PCI + Block Size + Separation Time

    elif isinstance(message, ErrorFrameMessage):
        pci_byte = 0x7F  # Error frame identifier
        bits.frombytes(bytes([pci_byte, message.serviceId, message.errorCode]))  # PCI + Service ID + Error Code

    else:
        raise ValueError("Unsupported message type for conversion to bitarray.")

    return bits


# Example data
data = bitarray()
data.frombytes(bytearray([0x01, 0x02, 0x03, 0x04]))  # Some example data

# Create a SingleFrameMessage object
message = SingleFrameMessage(dataLength=len(data) // 8, data=data)

# Convert message to bitarray
bit_data = message_to_bitarray(message)

# Print the bitarray result
print(bit_data)
