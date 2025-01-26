from typing import Callable, List, Union

# import can.message
from bitarray import bitarray
from Address import Address
from IsoTpConfig import IsoTpConfig
from ConsecutiveFrameMessage import ConsecutiveFrameMessage
from ErrorFrameMessage import ErrorFrameMessage
from FirstFrameMessage import FirstFrameMessage
from FlowControlFrameMessage import FlowControlFrameMessage
from FlowStatus import FlowStatus
from FrameMessage import FrameMessage
from FrameType import FrameType
from SingleFrameMessage import SingleFrameMessage
from RecvRequest import RecvRequest
from SendRequest import SendRequest
import can

def _parse_message(data: bitarray) -> Union[FrameMessage, None]:
    if not data or len(data) < 8:
        raise ValueError("The input bitarray is empty or invalid.")

    # Convert the first 8 bits to an integer (PCI Byte)
    pci_byte = int(data[:8].tobytes()[0])
    frame_type = (pci_byte >> 4) & 0xF

    if frame_type == FrameType.SingleFrame.value:
        # Single Frame
        data_length = pci_byte & 0xF
        frame_data = data[8:8 + (data_length * 8)]  # Extract data bits
        return SingleFrameMessage(dataLength=data_length, data=frame_data)

    elif frame_type == FrameType.FirstFrame.value:
        # First Frame
        if len(data) < 16:
            raise ValueError("Invalid First Frame: Insufficient data.")
        data_length = ((pci_byte & 0xF) << 8) | int(data[8:16].tobytes()[0])
        frame_data = data[16:]  # Extract remaining bits
        return FirstFrameMessage(dataLength=data_length, data=frame_data)

    elif frame_type == FrameType.ConsecutiveFrame.value:
        # Consecutive Frame
        sequence_number = pci_byte & 0xF
        frame_data = data[8:]  # Extract remaining bits
        return ConsecutiveFrameMessage(sequenceNumber=sequence_number, data=frame_data)

    elif frame_type == FrameType.FlowControlFrame.value:
        # Flow Control Frame
        if len(data) < 24:
            raise ValueError("Invalid Flow Control Frame: Insufficient data.")
        flow_status_value = pci_byte & 0xF
        flow_status = FlowStatus(flow_status_value)
        block_size = int(data[8:16].tobytes()[0])
        separation_time = int(data[16:24].tobytes()[0])
        return FlowControlFrameMessage(flowStatus=flow_status, blockSize=block_size, separationTime=separation_time)

    elif frame_type == 0x7F:
        # Error Frame
        if len(data) < 24:
            raise ValueError("Invalid Error Frame: Insufficient data.")
        service_id = int(data[8:16].tobytes()[0])
        error_code = int(data[16:24].tobytes()[0])
        return ErrorFrameMessage(serviceId=service_id, errorCode=error_code)

    else:
        raise ValueError(f"Unknown Frame Type: {frame_type}")


def message_to_bitarray(message: FrameMessage) -> bitarray:
    bits = bitarray()

    if isinstance(message, SingleFrameMessage):
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


def bytearray_to_bitarray(byte_data: bytearray) -> bitarray:
    # Initialize an empty bitarray
    bits = bitarray()
    
    # Loop through each byte and append its bits
    for byte in byte_data:
        # Convert the byte to bits and append to the bitarray
        bits.frombytes(byte.to_bytes(1, 'big'))
    
    return bits


def bitarray_to_bytearray(bits: bitarray) -> bytearray:
    # Convert the bitarray to bytes and then to bytearray
    return bytearray(bits.tobytes())


class IsoTp:
    def __init__(self, iso_tp_config: IsoTpConfig):
        self._config = iso_tp_config
        self._recv_requests: List[RecvRequest] = []
        self._send_requests: List[SendRequest] = []
        self._control_frames: List[tuple[Address, FlowControlFrameMessage]] = []  # List to store control frames and addresses

    
    def set_on_recv_success(self, fn: Callable):
        self._config.on_recv_success = fn


    def set_on_recv_error(self, fn: Callable):
        self._config.on_recv_error = fn


    def set_send_fn(self, fn: Callable):
        self._config.send_fn = fn

    
    def send(self, data: bitarray, address: Address, on_success: Callable, on_error: Callable):
        print(data)
        data = bytearray_to_bitarray(data)
        try:
            send_request = SendRequest(
                address=address,
                txfn=self._send_to_can,  # Can send function ( takes hex frame as a parameter)
                rxfn=self._get_control_frame_by_address,  # Function to read from can
                on_success=on_success,
                on_error=on_error,
                stmin=self._config.stmin,
                timeout=self._config.timeout,
                block_size=self._config.max_block_size,
            )
            self._send_requests.append(send_request)
            send_request.send(data)

            for request in self._send_requests:
                if request.is_finished() or request.has_received_error_frame():
                    self._send_requests.remove(request)

        except Exception as e:
            on_error(e)

    def recv(self, message: bitarray, address: Address):
        try:
            new_message = _parse_message(data=message)

            # Check if the message is a control frame
            if isinstance(new_message, FlowControlFrameMessage):
                # Add control frame and its address to the control frame list
                self._control_append((address, new_message))
                return  # Exit after storing the control frame
            elif isinstance(new_message, ErrorFrameMessage):
                for request in self._send_requests:
                    if request.get_address() == address:
                        request.set_received_error_frame(True)
                        return  # Exit

            # Check if there is an existing request with the same address
            for request in self._recv_requests:
                if request.get_address() == address:
                    if request.get_state() in {"ErrorState", "FinalState"}:
                        self._recv_requests.remove(request)
                        break
                    else:
                        # Process the message using the existing request
                        request.process(new_message)
                        return  # Exit after processing

            # If no existing request is found, create a new one
            new_request = RecvRequest(
                address=address,
                block_size=self._config.max_block_size,
                timeout=self._config.timeout,
                stmin=self._config.stmin,
                on_success=self._config.on_recv_success,
                on_error=self._config.on_recv_error,
                send_frame=self._send_frame
            )

            # Add the new request to the list
            self._recv_requests.append(new_request)

            # Process the message using the new request
            new_request.process(new_message)

        except Exception as e:
            self._config.on_recv_error()

    def _get_control_frame_by_address(self, address: Address) -> Union[FlowControlFrameMessage, None]:
        """
        Search for a control frame by its address in the control frame list.
        :param address: The address to search for.
        :return: The corresponding FlowControlFrameMessage if found, else None.
        """
        for addr, control_frame in self._control_frames:
            if addr == address:
                return control_frame
        return None

    def _send_frame(self, address: Address, frame: FrameMessage):
        message_in_bits = message_to_bitarray(frame)
        message_in_bytes = bitarray_to_bytearray(message_in_bits)
        self._config.send_fn(arbitration_id=address._txid, data=message_in_bytes)
        # can send here ( i have the address and the bits to send )


    def _send_to_can(self, address: Address, message):
        message = bytearray(message)  # Convert frame to bytearray
        self._config.send_fn(arbitration_id=address._txid, data=message)


    def recv_can_message(self, message: can.Message):
        """
        Process a received CAN message by extracting the data and arbitration ID.
        
        Args:
            message (can.Message): The CAN message object to process.
        """
        try:
            # Extract arbitration ID
            arbitration_id = message.arbitration_id
            # Convert data to bitarray
            data = message.data  # Data as bytes
            data_bits = bitarray()
            data_bits.frombytes(data)  # Convert bytes to bitarray

            address = Address(txid=arbitration_id, rxid=self._config.recv_id)

            self.recv(message=data_bits,address=address)

            # Add further processing logic here as needed
            # Example: call another function with the extracted information
            # self.handle_message(arbitration_id, data)
        except Exception as e:
            print(f"Error processing CAN message: {e}")



    def set_recv_id(self, recv_id):
        self._config.recv_id = recv_id
