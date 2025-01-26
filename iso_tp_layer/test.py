import time
from bitarray import bitarray
from IsoTpConfig import IsoTpConfig
from SingleFrameMessage import SingleFrameMessage
from IsoTp import IsoTp, message_to_bitarray
from Address import Address


# Callback functions
def on_success():
    print("Message sent successfully!")


def on_error(error):
    print(f"Error occurred: {error}")


# Create an IsoTpConfig instance
config = IsoTpConfig(
    max_block_size=8,
    timeout=1000,
    stmin=10,
    on_recv_success=on_success,
    on_recv_error=on_error
)
# Create an IsoTp instance
iso_tp = IsoTp(config)

# Define CAN address (Example: Normal 11-bit addressing mode)
address = Address(txid=0x123, rxid=0x456)

# Create a message (Example: Single Frame Message)
message_data = bitarray('1010101011100001')  # Example data
single_frame = SingleFrameMessage(dataLength=len(message_data) // 8, data=message_data)

# Convert the message to bitarray
bitarray_message = message_to_bitarray(single_frame)

# Send the message
iso_tp.send(data=bitarray_message, address=address, on_success=on_success, on_error=on_error)

# Simulate receiving a message (In real-world usage, you’d receive from the CAN bus)
time.sleep(1)
iso_tp.recv(bitarray_message, address)
