import socket
import threading


# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5001
BUFFER_SIZE = 1024

# Simulated stored versions on the server
server_versions = {
    "car_123": {
        "HMI": "3.5",
        "ECU1": "2.2",
        "ECU2": "3.0",
        "ECU3": "9.3",
        "ECU.n": "4.6"
    }
}


def handle_car_info(client_socket: socket, car_info: str):
    car_info = eval(car_info)  # Receive car info
    print(f"car_info: {car_info}")
    car_id = car_info["car_id"]
    updates_needed = {}

    if car_id in server_versions:
        for ecu, version in car_info.items():
            if ecu != "car_id" and ecu in server_versions[car_id]:
                if version != server_versions[car_id][ecu]:
                    updates_needed[ecu] = server_versions[car_id][ecu]

    print(f"str(updates_needed).encode(): {str(updates_needed).encode()}")
    client_socket.send(str(updates_needed).encode())  # Send required updates


def send_update(client_socket: socket, ecu: str):
    update_data = f"New data for {ecu} version {server_versions['car_123'][ecu]}"
    client_socket.send(update_data.encode())


def handle_client(client_socket: socket):
    while True:
        request_type = client_socket.recv(BUFFER_SIZE).decode()
        print(f"request_type: {request_type}")
        if request_type.startswith("CAR_INFO"):
            car_info = request_type.split("-")[1]
            handle_car_info(client_socket, car_info)
            print("updates_needed sent successfully ")
        elif request_type.startswith("REQUEST_UPDATE"):
            ecu = request_type.split("-")[1]
            send_update(client_socket, ecu)
        elif request_type.startswith("EXIT"):
            print("Received Exit")
            break

    client_socket.close()


def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"[*] Server listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[*] Connection accepted from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()


if __name__ == "__main__":
    server()
