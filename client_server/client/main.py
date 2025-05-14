import argparse
from client import ECUUpdateClient

def main():
    parser = argparse.ArgumentParser(description='ECU Update Client')
    parser.add_argument('--server-host', default='localhost', help='Server host')
    parser.add_argument('--server-port', type=int, default=5000, help='Server port')
    parser.add_argument('--data-dir', default='./client_data', help='Data directory')
    
    args = parser.parse_args()

    client = ECUUpdateClient(args.server_host, args.server_port, args.data_dir)
    try:
        client.start()
        # Keep main thread alive
        while True:
            input()  
    except KeyboardInterrupt:
        print("\nShutting down client...")
        client.shutdown()

if __name__ == "__main__":
    main()