import os
import json
import random

def create_directory_structure():
    """Create the client data directory structure"""
    base_dir = "client_data"
    dirs = [
        "",
        "ecu_versions",
        "ecu_versions/Engine_Control_Module/1.0.0",
        "ecu_versions/Transmission_Control_Module/1.0.0",
        "ecu_versions/Brake_Control_Module/1.0.0",
        "temp_downloads",
        "backups"
    ]
    
    for dir_path in dirs:
        full_path = os.path.join(base_dir, dir_path)
        os.makedirs(full_path, exist_ok=True)

def generate_hex_file(directory, size_kb=100):
    """Generate a sample hex file"""
    hex_data = bytes([random.randint(0, 255) for _ in range(size_kb * 1024)])
    with open(os.path.join(directory, "hex_file.hex"), 'wb') as f:
        f.write(hex_data)

def write_json_file(file_path, data):
    """Write JSON data to file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def main():
    # Create directory structure
    create_directory_structure()

    
    # Generate hex files for each ECU version
    ecu_dirs = [
        "client_data/ecu_versions/Engine_Control_Module/1.0.0",
        "client_data/ecu_versions/Transmission_Control_Module/1.0.0",
        "client_data/ecu_versions/Brake_Control_Module/1.0.0"
    ]
    
    for dir_path in ecu_dirs:
        generate_hex_file(dir_path)

if __name__ == "__main__":
    main()
    