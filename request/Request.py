from bitarray import bitarray
from InitialState import InitialState
from frames.FrameMessage import FrameMessage
from Address import Address


class Request:
    """
    Represents a request containing a bitarray message and a state.
    """
    def __init__(self, address: Address):
        self._message = bitarray()  # Initialize with an empty bitarray
        self._state = InitialState()  # Start with the initial state
        self._address = address

    def set_state(self, state):
        """
        Change the state of the request.
        """
        self._state = state
        print(f"State has been changed to {state.__class__.__name__}")

    def get_state(self):
        return self._state.__class__.__name__

    def set_address(self, address: Address):
        self._address = address
        print(f"Address has been changed to {address}")


    def append_bits(self, bits: str):
        """
        Append bits to the message.
        """
        self._message.extend(bits)
        print(f"Bits appended: {bits}")
        print(f"Current message: {self._message.to01()}")

    def process(self, frameMessage: FrameMessage):
        """
        Delegate processing to the current state.
        The state will modify the request as needed.
        """
        self._state.handle(self, frameMessage)
