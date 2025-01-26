from bitarray import bitarray

from Address import Address
from iso_tp_layer.send_request.SendRequest import SendRequest
import time


# Mock transmit function
def mock_txfn(frame, message):
    print(f"Transmitted frame: {frame}")


# Mock receive functions
def mock_rxfn_continue(address: Address):
    """Simulating a Flow Control frame with Continue (0x30), BlockSize = 3, STmin = 5ms."""
    return bytes([0x30, 3, 5])


def mock_rxfn_wait(address: Address):
    """Simulating a Flow Control frame with Wait (0x31), BlockSize = 0, STmin = 10ms."""
    return bytes([0x31, 2, 10])


def mock_rxfn_abort(address: Address):
    """Simulating a Flow Control frame with Abort (0x32), BlockSize = 0, STmin = 0."""
    return bytes([0x32, 0x00, 0x00])


# Success and error callbacks
def on_success():
    print("✅ Transmission successful!")


def on_error(error):
    print(f"❌ Transmission failed: {error}")


address = Address(addressing_mode=0x00, txid=0x123, rxid=0x456)  # Replace 0x00 with the appropriate mode

# Test Cases
# print("\n=== Test Case 1: Single-frame Message ===")
# data_single = bitarray('11010011')  # 8 bits (fits in one frame)
# sender_single = SendRequest(
#     txfn=mock_txfn, rxfn=mock_rxfn_continue, on_success=on_success, on_error=on_error, tx_padding=0xAA
# )
# sender_single.send(data_single)

print("\n=== Test Case 2: Multi-frame Message (Flow Control: Continue) ===")
# Hex representation of the binary data
hex_data_multi_continue = "D3 97 47 8E 8D 4A D3 97 47 8E 8D 4A D3 97 D3 97 47 8E 8D 4A D3 97 47 8E 8D 4A D3 97 D3 97 47 8E 8D 4A D3 97 47 8E 8D 4A D3 97"
# Convert hex to bitarray
data_multi_continue = bitarray()
data_multi_continue.frombytes(bytes.fromhex(hex_data_multi_continue))

sender_multi_continue = SendRequest(
    txfn=mock_txfn, rxfn=mock_rxfn_continue, on_success=on_success, on_error=on_error, stmin=5, block_size=3, address=address
)
sender_multi_continue.send(data_multi_continue)

while True:
    time.sleep(100)

# print("\n=== Test Case 3: Multi-frame Message (Flow Control: Wait) ===")
# data_multi_wait = bitarray('110100111001011101000111100011101000110101001010110100111001011101000111100011101000110101001010')  # More than 7 bytes
# sender_multi_wait = SendRequest(
#     txfn=mock_txfn, rxfn=mock_rxfn_wait, on_success=on_success, on_error=on_error, stmin=10, block_size=3, tx_padding=0xAA
# )
# try:
#     sender_multi_wait.send(data_multi_wait)
# except ValueError as e:
#     print(f"❌ Error: {e}")
#
# print("\n=== Test Case 4: Multi-frame Message (Flow Control: Abort) ===")
# data_multi_abort = bitarray('110100111001011101000111100011101000110101001010110100111001011101000111100011101000110101001010')  # More than 7 bytes
# sender_multi_abort = SendRequest(
#     txfn=mock_txfn, rxfn=mock_rxfn_abort, on_success=on_success, on_error=on_error, stmin=0, block_size=3, tx_padding=0xAA
# )
# try:
#     sender_multi_abort.send(data_multi_abort)
# except ValueError as e:
#     print(f"❌ Error: {e}")
