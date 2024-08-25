import sys
import os
from hex_parser.SRecordParser import DataRecord, SRecordParser
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from delta_generator.DeltaGenerator import DeltaGenerator, DeltaAlgorithm
from compressor.compressor import Compressor, CompressionAlgorithm

def main():
    # original_data = bytearray(b"Hello from Python! This will be decompressed in C. 3")
    # print(original_data)

    # compressor=Compressor(algorithm=CompressionAlgorithm.LZ4)
    # compressed_data=compressor.compress(data=original_data)
    # print("compressed data :::")
    # print(compressed_data)
    # print(f"{[hex(x) for x in compressed_data]}")
    # data=compressor.decompress(data=compressed_data)
    # print(" data :::")
    # print(data)
    # print(f"{[hex(x) for x in data]}")
    parser = SRecordParser()
    parser2 = SRecordParser()
    parser.parse_file(filename="/home/debian/Desktop/SDVSOTA/ISO-TP-lib/old_app.srec")
    old_data=parser.get_merged_records()
    # print(f"len(delta_records) {len(old_data)}")
    # print(old_data)
    parser2.parse_file(filename="/home/debian/Desktop/SDVSOTA/ISO-TP-lib/new_app.srec")
    new_data=parser2.get_merged_records()
    # print(f"len(delta_records) {len(new_data)}") 
    # print(new_data) 
    deltagenerator=DeltaGenerator(algorithm=DeltaAlgorithm.SENDING_COMPLETE_SECTOR)
    print('#'*100)
    delta_records=deltagenerator.generate_delta(old_version=old_data,new_version=new_data)
    print(len(delta_records[0].data))
    compressor=Compressor(algorithm=CompressionAlgorithm.LZ4)
    deCompressed_data=compressor.compress(data=delta_records[0].data)
    print(len(deCompressed_data))
    print('#'*100)
    # print(f"len(delta_records) {len(delta_records)}")
    # print(delta_records)
    # print("data :::")
    # print([hex(x) for x in delta_records[1].data])
    # compressor=Compressor(algorithm=CompressionAlgorithm.LZ4)
    # compressed_data=compressor.compress(data=delta_records[1].data)
    print("*"*100)
    print(f"old {old_data[11].data}")
    # print("compressed data :::")
    # print(f"{[hex(x) for x in compressed_data]}")
    # print(len(delta_records[1].data))
    # print(len(compressed_data))



if __name__ == "__main__":
    main()
