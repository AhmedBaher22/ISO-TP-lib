import socket

# Client configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5001
BUFFER_SIZE = 1024

car_info = {
    "car_id": "car_123",
    "HMI": "3.4",
    "ECU1": "2.2",
    "ECU2": "2.9",
    "ECU3": "9.3",
    "ECU.n": "4.6"
}


def send_car_info(client_socket: socket):
    client_socket.send(b"CAR_INFO-")  # Indicate car info is being sent
    client_socket.send(str(car_info).encode())
    recv_msg = client_socket.recv(BUFFER_SIZE).decode()
    print(recv_msg)
    return eval(recv_msg)


def request_updates(client_socket: socket, updates_needed):
    for ecu, new_version in updates_needed.items():
        client_socket.send(f"REQUEST_UPDATE-{ecu}".encode())
        data = client_socket.recv(BUFFER_SIZE).decode()
        print(f"Received updated data for {ecu}: {data}")
        car_info[ecu] = new_version
        print(f"Updated {ecu} to version {new_version}")


def client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    updates_needed = send_car_info(client_socket)
    print("Updates needed:", updates_needed)

    request_updates(client_socket, updates_needed)
    client_socket.send("EXIT".encode())
    client_socket.close()
    print(f"car_info: {car_info}")


if __name__ == "__main__":
    client()
