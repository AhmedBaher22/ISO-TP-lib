import argparse
from server import ECUUpdateServer

def main():
    parser = argparse.ArgumentParser(description='ECU Update Server')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=5000, help='Server port')
    parser.add_argument('--data-dir', default='./data', help='Data directory')
    
    args = parser.parse_args()

    server = ECUUpdateServer(args.host, args.port, args.data_dir)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == "__main__":
    main()