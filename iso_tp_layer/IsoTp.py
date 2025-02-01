from typing import Callable, List, Union
from bitarray import bitarray
import sys
import os
import threading
import can
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.Address import Address
from iso_tp_layer.IsoTpConfig import IsoTpConfig
from iso_tp_layer.frames.ConsecutiveFrameMessage import ConsecutiveFrameMessage
from iso_tp_layer.frames.FirstFrameMessage import FirstFrameMessage
from iso_tp_layer.frames.FlowControlFrameMessage import FlowControlFrameMessage
from iso_tp_layer.frames.FlowStatus import FlowStatus
from iso_tp_layer.frames.FrameMessage import FrameMessage
from iso_tp_layer.frames.FrameType import FrameType
from iso_tp_layer.frames.SingleFrameMessage import SingleFrameMessage
from iso_tp_layer.recv_request.RecvRequest import RecvRequest
from iso_tp_layer.send_request.SendRequest import SendRequest
from iso_tp_layer.IsoTpLogger import IsoTpLogger
from iso_tp_layer.Exceptions import IsoTpException


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
        bits.frombytes(
            bytes([pci_byte, message.blockSize, message.separationTime]))  # PCI + Block Size + Separation Time

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
        self._control_frames: List[
            tuple[Address, FlowControlFrameMessage]] = []  # List to store control frames and addresses
        self.logger = IsoTpLogger()
        self.lock = threading.Lock()
        self.logger.log_initialization("IsoTp instance initialized with provided configuration.")


    def set_on_recv_success(self, fn: Callable):
        self._config.on_recv_success = fn

    def set_on_recv_error(self, fn: Callable):
        self._config.on_recv_error = fn

    def set_send_fn(self, fn: Callable):
        self._config.send_fn = fn

    def send(self, data: bitarray, address: Address, on_success: Callable, on_error: Callable):
        data = bytearray_to_bitarray(data)
        try:
            self.logger.log_info(f"Sending message to {address} with data: {data}")
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

            self.logger.log_info(f"Successfully sent message to {address}")

        except Exception as e:
            self.logger.log_error(IsoTpException(f"Error while sending message to {address}: {e}"))
            on_error(e)

    def recv(self, message: bitarray, address: Address):
        try:
            self.logger.log_info(f"Receiving message from {address}")

            new_message = _parse_message(data=message)

            with self.lock:  # Ensure thread safety
                # Check if the message is a control frame
                if isinstance(new_message, FlowControlFrameMessage):
                    self.logger.log_debug(f"Received Flow Control Frame from {address}: {new_message}")
                    self._control_frames.append((address, new_message))  # Safe addition

                    if new_message.flowStatus == FlowStatus.Abort:
                        self.logger.log_warning(f"Flow control frame indicates abort from {address}")
                        for request in self._send_requests:
                            if request.get_address() == address:
                                request.set_received_error_frame(True)
                                return  # Exit
                    return

                # Check if there is an existing request with the same address
                for request in self._recv_requests:
                    if request.get_address() == address:
                        if request.get_state() in {"ErrorState", "FinalState"}:
                            self.logger.log_debug(f"Removing completed request from {address}")
                            self._recv_requests.remove(request)  # Safe removal
                            break
                        else:
                            self.logger.log_debug(f"Processing message with existing request for {address}")
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
                self._recv_requests.append(new_request)  # Safe addition
                self.logger.log_info(f"Created new request for {address}")

            # Process the message using the new request (outside the lock to avoid blocking other threads)
            new_request.process(new_message)

        except Exception as e:
            self.logger.log_error(IsoTpException(f"Error while sending message to {address}: {e}"))
            self._config.on_recv_error(e)

    def _get_control_frame_by_address(self, address: Address) -> Union[FlowControlFrameMessage, None]:
        """
        Search for a control frame by its address in the control frame list.
        :param address: The address to search for.
        :return: The corresponding FlowControlFrameMessage if found, else None.
        """
        self.logger.log_debug(f"Searching for control frame for address {address}")

        for addr, control_frame in self._control_frames:
            if addr == address:
                self.logger.log_debug(f"Found control frame for {address}")
                return control_frame
        self.logger.log_warning(f"No control frame found for address {address}")
        return None

    def _send_frame(self, address: Address, frame: FrameMessage):
        message_in_bits = message_to_bitarray(frame)
        message_in_bytes = bitarray_to_bytearray(message_in_bits)
        self.logger.log_info(f"Sending frame to {address}: {frame}")
        self.logger.log_debug(f"Frame in bits: {message_in_bits}")
        self.logger.log_debug(f"Frame in bytes: {message_in_bytes}")
        self._config.send_fn(arbitration_id=address._txid, data=message_in_bytes)


    def _send_to_can(self, address: Address, message):
        message = bytearray.fromhex(message)  # Convert frame to bytearray
        self._config.send_fn(arbitration_id=address._txid, data=message)


    def recv_can_message(self, message: can.Message):
        """
        Process a received CAN message in a separate thread.

        Args:
            message (can.Message): The CAN message object to process.
        """

        def process_message():
            """Function to process the message in a new thread."""
            try:
                # Extract arbitration ID
                arbitration_id = message.arbitration_id

                # Convert data to bitarray
                data = message.data  # Data as bytes
                data_bits = bitarray()
                data_bits.frombytes(data)  # Convert bytes to bitarray

                # Create Address object
                address = Address(txid=arbitration_id, rxid=self._config.recv_id)

                # Process the message
                self.recv(message=data_bits, address=address)

            except Exception as e:
                print(f"Error processing CAN message: {e}")
        # Create a new thread and start it
        thread = threading.Thread(target=process_message, daemon=True, name="WorkerThread")
        thread.start()
        # print(threading.current_thread())
        # for thread in threading.enumerate():
        #     print(f"Thread Name: {thread.name}, ID: {thread.ident}, Is Daemon: {thread.daemon}")

    def set_recv_id(self, recv_id):
        self._config.recv_id = recv_id
