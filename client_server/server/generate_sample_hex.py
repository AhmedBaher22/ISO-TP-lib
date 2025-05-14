import os
import random


def generate_hex_file(file_path, size_kb=100):
    """Generate a sample hex file of specified size"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Generate random hex data
    hex_data = bytes([random.randint(0, 255) for _ in range(size_kb * 1024)])

    with open(file_path, 'wb') as f:
        f.write(hex_data)


def main():
    # List of hex files from versions.json
    hex_dir = "hex_files"

    hex_files = [
        os.path.join(hex_dir, "ECM_1_0_0.srec"),
        os.path.join(hex_dir, "ECM_1_1_0.srec"),
        os.path.join(hex_dir, "ECM_1_2_0.srec"),
        os.path.join(hex_dir, "TCM_1_0_0.srec"),
        os.path.join(hex_dir, "TCM_1_1_0.srec"),
        os.path.join(hex_dir, "BCM_1_0_0.srec"),
        os.path.join(hex_dir, "BCM_1_1_0.srec"),
        os.path.join(hex_dir, "BMS_1_0_0.srec"),
        os.path.join(hex_dir, "BMS_1_1_0.srec"),
        os.path.join(hex_dir, "BMS_1_2_0.srec")
    ]

    # Generate each hex file
    for file_path in hex_files:
        generate_hex_file(file_path)
        print(f"Generated: {file_path}")


if __name__ == "__main__":
    main()
