from enum import Enum
import lz4.frame

class CompressionAlgorithm(Enum):
    LZ4 = 'lz4'

class Compressor:
    def __init__(self, algorithm: CompressionAlgorithm):
        self.algorithm = algorithm

    def compress(self, data: bytearray) -> bytearray:
        if self.algorithm == CompressionAlgorithm.LZ4:
            compressed = lz4.frame.compress(bytes(data),)
            return bytearray(compressed)
        else:
            raise NotImplementedError(f"Compression for {self.algorithm} is not implemented.")

    def decompress(self, data: bytearray) -> bytearray:
        if self.algorithm == CompressionAlgorithm.LZ4:
            decompressed = lz4.frame.decompress(bytes(data))
            return bytearray(decompressed)
        else:
            raise NotImplementedError(f"Decompression for {self.algorithm} is not implemented.")

if __name__ == "__main__":
    # Generate a large bytearray using hexadecimal format
    hex_string = (
        "deadbeefcafebabe" * 1000  # repeating pattern to increase size
        + "11223344556677889900aabbccddeeff" * 500
        + "0f0e0d0c0b0a09080706050403020100" * 250
    )
    
    large_data = bytearray.fromhex(hex_string)
    print(type(large_data))
    print(large_data)
    print('*'*100)
    compressor = Compressor(CompressionAlgorithm.LZ4)
    compressed = compressor.compress(large_data)
    print(type(compressed))
    print(compressed)
    print('*'*100)
    print(f"Original Size: {len(large_data)} bytes")
    print(f"Compressed Size: {len(compressed)} bytes")
    
    decompressed = compressor.decompress(compressed)
    print(type(decompressed))
    print(decompressed)
    print('*'*100)
    print(f"Decompressed Size: {len(decompressed)} bytes")
    
    assert decompressed == large_data
    print(" Decompressed data matches original!")

    original_data = bytearray(b"Hello from Python! This will be decompressed in C. 3")
    print(original_data)

    compressor=Compressor(algorithm=CompressionAlgorithm.LZ4)
    compressed_data=compressor.compress(data=original_data)
    print("compressed data :::")
    print(compressed_data)
    print(f"{[hex(x) for x in compressed_data]}")
    data=compressor.decompress(data=compressed_data)
    print(" data :::")
    print(data)
    print(f"{[hex(x) for x in data]}")
