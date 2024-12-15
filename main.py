from Address import Address
from AddressingMode import AddressingMode
from Transport import Transport


def my_txfn(frame: str):
    pass
    # print(f"Transmitted Frame: {frame}")


def my_rxfn():
    print("Receiving data...")
    return b"Received data"


# Initialize address and transport
address = Address(addressing_mode=AddressingMode.Normal_11bits, txid=0x123, rxid=0x456)
transport = Transport(address, txfn=my_txfn, rxfn=my_rxfn)

transport.send(0x5555)


def send_file(file_path: str):
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


# send_file("main.py")

