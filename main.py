from Address import Address
from AddressingMode import AddressingMode
from Transport import Transport


def main():
    # Define test transmit and receive functions
    def test_txfn(frame: str):
        print(f"Transmitted Frame: {frame}")

    def test_rxfn():
        # Example of received frames in bytes
        test_frames = [

            b"\x10\x14\xAA\xBB\xCC\xDD\xEE\xFF",  # First frame
            b"\x20\x11\x22\x33\x44\x55\x66\x77",  # Consecutive frame 0
            b"\x24\x88\x99\xAA\xBB\xCC\xDD\xEE"   # Consecutive frame 1
        ]
        # Simulate receiving each frame one at a time
        if main.rx_index < len(test_frames):
            frame = test_frames[main.rx_index]
            main.rx_index += 1
            return frame
        return b""  # Simulate end of data

    main.rx_index = 0  # Counter for test_rxfn

    # Initialize the address and transport
    address = Address(addressing_mode=0x00, txid=0x123, rxid=0x456)  # Replace 0x00 with the appropriate mode
    transport = Transport(address, txfn=test_txfn, rxfn=test_rxfn)

    # Test Scenario 1: Send a single-frame message
    print("\nTest Scenario 1: Sending Single-Frame Message")
    transport.send(0xABCD)

    # Test Scenario 2: Send a multi-frame message
    print("\nTest Scenario 2: Sending Multi-Frame Message")
    transport.send(0x123456789ABCDEF012345678)

    # Test Scenario 3: Send a Flow Control frame
    print("\nTest Scenario 3: Sending Flow Control Frame")
    transport._send_control_frame(flow_status=0x0, block_size=0x10, separation_time=0x05)

    # Test Scenario 4: Receive a multi-frame message
    # print("\nTest Scenario 4: Receiving Multi-Frame Message")
    # try:
    #     message = transport.recv()
    #     print(f"Received Complete Message: {message.hex().upper()}")
    # except Exception as e:
    #     print(f"Error during reception: {e}")


rflag= True
def send_file(file_path: str):
    def test_txfn(frame: str):
        print(f"Transmitted Frame: {frame}")

    def test_rxfn():
        # Example of received frames in bytes
        test_frames = [
            b"\x30\x02\x00\x00\x00\xDD\xEE\xFF",
            b"\x31\x00\x00\xBB\xCC\xDD\xEE\xFF",
            # b"\x10\x14\xAA\xBB\xCC\xDD\xEE\xFF",  # First frame
            # b"\x20\x11\x22\x33\x44\x55\x66\x77",  # Consecutive frame 0
            # b"\x24\x88\x99\xAA\xBB\xCC\xDD\xEE"   # Consecutive frame 1
        ]

        # Simulate receiving each frame one at a time
        # if main.rx_index < len(test_frames):
        #     frame = test_frames[main.rx_index]
        #     main.rx_index += 1
        global rflag
        if rflag:
            rflag=False

            return test_frames[1]

        return test_frames[0]

        return b""  # Simulate end of data


    # Initialize the address and transport
    address = Address(addressing_mode=0x00, txid=0x123, rxid=0x456)  # Replace 0x00 with the appropriate mode
    transport = Transport(address, txfn=test_txfn, rxfn=test_rxfn)
    try:
        with open(file_path, "rb") as file:  # Open the file in binary mode
            # Read the entire file content
            file_data = file.read()

            # Convert the binary data to a hexadecimal string
            hex_data = file_data.hex().upper()  # Convert to uppercase hexadecimal
            print(f"Sending entire file as hex: {hex_data}")  # Debug: Show the hex string

            # Convert the hex string to an integer and send it
            try:
                data_int = int(hex_data, 16)
                transport.send(data_int)  # Send the entire file as a single integer
            except ValueError as e:
                print(f"Error converting file data to integer: {e}")
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"Error while reading the file: {e}")



if __name__ == "__main__":
    send_file("receive.py")
    # main()

