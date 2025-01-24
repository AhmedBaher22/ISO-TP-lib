from Request import Request
from Address import Address
from frames.SingleFrameMessage import SingleFrameMessage
from bitarray import bitarray

# Initialize the address and transport
address = Address(addressing_mode=0x00, txid=0x123, rxid=0x456)  # Replace 0x00 with the appropriate mode
request = Request(address)
print(request.get_state())
request.process(SingleFrameMessage(dataLength=8, data=bitarray('110110')))
print(request.get_state())
