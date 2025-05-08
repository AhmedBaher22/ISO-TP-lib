import lz4.block
import time
import binascii

def hex_dump(data, max_bytes=64, prefix=""):
    """Print a hex dump of the data for debugging."""
    hex_str = binascii.hexlify(data[:max_bytes]).decode()
    formatted = ' '.join([hex_str[i:i+2] for i in range(0, len(hex_str), 2)])
    print(f"{prefix}{formatted}")
    if len(data) > max_bytes:
        print(f"{prefix}... ({len(data)} bytes total)")

def reverse_engineer_lz4_block_format(data):
    """Analyze the given data for LZ4 block format."""
    print("\nLZ4 Block Format Analysis:")
    
    # Let's analyze the library's compressed format
    print(f"Full hex: {binascii.hexlify(data).decode()}")
    print(f"Length: {len(data)} bytes")
    
    # Analyze what appears to be a header
    if len(data) >= 4:
        print(f"First bytes: {data[0]:02x} {data[1]:02x} {data[2]:02x} {data[3]:02x}")
    
    # Try to find token bytes
    for i in range(len(data)):
        token = data[i]
        literal_length = token >> 4
        match_length = (token & 0x0F) + 4  # In LZ4, match length is stored -4
        print(f"Position {i}: Token {token:02x} - Literal length {literal_length}, Match length {match_length}")
        
        # Skip over this token's data
        i += 1
        
        # Skip over extended literal length bytes if any
        if literal_length == 15:
            while i < len(data) and data[i] == 255:
                i += 1
            i += 1  # Skip the final extended length byte
        
        # Skip over literal bytes
        i += literal_length
        
        # Skip over match offset
        i += 2
        
        # Skip over extended match length bytes if any
        if match_length == 19:  # 15 + 4
            while i < len(data) and data[i] == 255:
                i += 1
            i += 1  # Skip the final extended length byte
    
    # Now let's try to decompose the library output to understand its structure
    test_data = b"ABCDABCDABCDABCD"
    library_compressed = lz4.block.compress(test_data)
    
    print("\nTest with simple repeating pattern:")
    print(f"Original: {binascii.hexlify(test_data).decode()}")
    print(f"Compressed: {binascii.hexlify(library_compressed).decode()}")
    
    # Attempt to manually decompress
    print("\nManual decompression attempt:")
    position = 0
    output = bytearray()
    
    # Get the uncompressed size
    uncompressed_size = library_compressed[0] | (library_compressed[1] << 8) | (library_compressed[2] << 16) | (library_compressed[3] << 24)
    print(f"Uncompressed size from header: {uncompressed_size}")
    position = 4  # Skip header
    
    while position < len(library_compressed):
        # Read token
        token = library_compressed[position]
        position += 1
        print(f"Token: {token:02x}")
        
        # Decode literal length
        literal_length = token >> 4
        print(f"  Literal length: {literal_length}")
        
        if literal_length == 15:
            # Handle extended length
            while position < len(library_compressed):
                extra = library_compressed[position]
                position += 1
                literal_length += extra
                if extra != 255:
                    break
            print(f"  Extended literal length: {literal_length}")
        
        # Copy literals
        print(f"  Copying {literal_length} literals from position {position}")
        output.extend(library_compressed[position:position + literal_length])
        print(f"  Literals: {binascii.hexlify(library_compressed[position:position + literal_length]).decode()}")
        position += literal_length
        
        # Check if we're at the end
        if position >= len(library_compressed):
            print("  End of compressed data")
            break
        
        # Read match offset
        match_offset = library_compressed[position] | (library_compressed[position + 1] << 8)
        position += 2
        print(f"  Match offset: {match_offset}")
        
        # Decode match length
        match_length = (token & 0x0F) + 4  # In LZ4, match length is stored -4
        print(f"  Initial match length: {match_length}")
        
        if (token & 0x0F) == 15:
            # Handle extended length
            while position < len(library_compressed):
                extra = library_compressed[position]
                position += 1
                match_length += extra
                if extra != 255:
                    break
            print(f"  Extended match length: {match_length}")
        
        # Copy match
        print(f"  Copying {match_length} bytes from output at (current position - {match_offset})")
        current_out_pos = len(output)
        for i in range(match_length):
            byte_to_copy = output[current_out_pos - match_offset + i]
            output.append(byte_to_copy)
    
    print(f"Decompressed: {binascii.hexlify(output).decode()}")
    print(f"Correct: {output == test_data}")
    
    return uncompressed_size  # Return the detected uncompressed size


def lz4_block_compress(data):
    """
    LZ4 block format compatible compression.
    
    Args:
        data: bytes or bytearray to compress
        
    Returns:
        bytearray containing compressed data in LZ4 block format
    """
    if isinstance(data, bytes):
        data = bytearray(data)
    
    # Initialize the output with uncompressed size (4 bytes, little endian)
    output = bytearray()
    size = len(data)
    output.append(size & 0xFF)
    output.append((size >> 8) & 0xFF)
    output.append((size >> 16) & 0xFF)
    output.append((size >> 24) & 0xFF)
    
    # Initialize variables
    position = 0
    hash_table = {}  # Maps 4-byte sequences to their positions
    literal_start = 0
    
    # Constants
    MIN_MATCH = 4
    
    while position <= len(data) - MIN_MATCH:
        # Create a simple hash of current 4 bytes
        h = (data[position] << 8) | data[position + 1]
        
        match_found = False
        match_offset = 0
        match_length = 0
        
        # Find a match in the hash table
        if h in hash_table:
            match_pos = hash_table[h]
            # Verify the match - required to handle hash collisions
            if match_pos >= position - 65536 and data[match_pos:match_pos + MIN_MATCH] == data[position:position + MIN_MATCH]:
                # Extend the match as far as possible
                match_length = MIN_MATCH
                while (position + match_length < len(data) and 
                       match_pos + match_length < position and
                       data[match_pos + match_length] == data[position + match_length] and
                       match_length < 65539):  # LZ4 limit
                    match_length += 1
                
                match_offset = position - match_pos
                match_found = True
        
        # Update hash table
        hash_table[h] = position
        
        if match_found and match_length >= MIN_MATCH:
            # We found a match, output literals and then the match
            literal_length = position - literal_start
            
            # Create token
            token = bytearray(1)
            token[0] = min(literal_length, 15) << 4  # Upper 4 bits = literal length
            token[0] |= min(match_length - MIN_MATCH, 15)  # Lower 4 bits = match length - 4
            
            output.extend(token)
            
            # Output extended literal length if needed
            if literal_length >= 15:
                length = literal_length - 15
                while length >= 255:
                    output.append(255)
                    length -= 255
                output.append(length)
            
            # Output literals
            if literal_length > 0:
                output.extend(data[literal_start:position])
            
            # Output match offset (2 bytes, little-endian)
            output.append(match_offset & 0xFF)
            output.append((match_offset >> 8) & 0xFF)
            
            # Output extended match length if needed
            if match_length - MIN_MATCH >= 15:
                length = match_length - MIN_MATCH - 15
                while length >= 255:
                    output.append(255)
                    length -= 255
                output.append(length)
            
            # Update positions
            position += match_length
            literal_start = position
        else:
            # No match or match too small, continue to next position
            position += 1
    
    # Handle remaining literals
    literal_length = len(data) - literal_start
    if literal_length > 0:
        # Create token (no match, just literals)
        token = bytearray(1)
        token[0] = min(literal_length, 15) << 4  # Upper 4 bits = literal length
        
        output.extend(token)
        
        # Output extended literal length if needed
        if literal_length >= 15:
            length = literal_length - 15
            while length >= 255:
                output.append(255)
                length -= 255
            output.append(length)
        
        # Output literals
        output.extend(data[literal_start:])
    
    return output


def lz4_block_decompress(compressed_data, expected_size=None):
    """
    LZ4 block format compatible decompression.
    
    Args:
        compressed_data: bytes or bytearray containing compressed data
        expected_size: optional expected size of decompressed data
        
    Returns:
        bytearray containing decompressed data
    """
    if isinstance(compressed_data, bytes):
        compressed_data = bytearray(compressed_data)
    
    # Get uncompressed size from header
    if expected_size is None:
        expected_size = (compressed_data[0] | 
                          (compressed_data[1] << 8) | 
                          (compressed_data[2] << 16) | 
                          (compressed_data[3] << 24))
    
    # Initialize output buffer
    output = bytearray()
    position = 4  # Skip the 4-byte header
    
    while position < len(compressed_data):
        # Read token
        token = compressed_data[position]
        position += 1
        
        # Decode literal length
        literal_length = token >> 4
        if literal_length == 15:
            while position < len(compressed_data):
                extra = compressed_data[position]
                position += 1
                literal_length += extra
                if extra != 255:
                    break
        
        # Copy literals
        output.extend(compressed_data[position:position + literal_length])
        position += literal_length
        
        # Check if we're at the end
        if position >= len(compressed_data):
            break
        
        # Read match offset
        match_offset = compressed_data[position] | (compressed_data[position + 1] << 8)
        position += 2
        
        if match_offset == 0:
            raise ValueError("Invalid match offset 0")
            
        # Decode match length
        match_length = (token & 0x0F) + 4  # In LZ4, match length is stored -4
        if (token & 0x0F) == 15:
            while position < len(compressed_data):
                extra = compressed_data[position]
                position += 1
                match_length += extra
                if extra != 255:
                    break
        
        # Copy match - handle overlapping matches
        curr_pos = len(output)
        for i in range(match_length):
            output.append(output[curr_pos - match_offset + i])
    
    # Verify correct decompression
    if expected_size != len(output):
        print(f"WARNING: Expected size {expected_size} but got {len(output)}")
    
    return output


def test_compatibility():
    """Test the compatibility of our implementation with the library."""
    # Test data
    test_data = b"ABCDABCDABCDABCD"  # Simple repeating pattern
    
    print("\n=== Testing LZ4 Block Format Compatibility ===")
    
    # First, let's analyze the library's format
    library_compressed = lz4.block.compress(test_data)
    uncompressed_size = reverse_engineer_lz4_block_format(library_compressed)
    
    print("\n=== Compressing with our implementation ===")
    our_compressed = lz4_block_compress(test_data)
    hex_dump(our_compressed, prefix="Our compressed: ")
    
    print("\n=== Compressing with library ===")
    lib_compressed = lz4.block.compress(test_data)
    hex_dump(lib_compressed, prefix="Library compressed: ")
    
    print("\n=== Compatibility Tests ===")
    
    # Test if library can decompress our data
    try:
        lib_decompressed = lz4.block.decompress(bytes(our_compressed))
        if lib_decompressed == test_data:
            print("SUCCESS: Library successfully decompressed our compressed data")
        else:
            print(f"FAILURE: Library decompression produced incorrect output: {lib_decompressed}")
    except Exception as e:
        print(f"FAILURE: Library couldn't decompress our data: {str(e)}")
    
    # Test if our implementation can decompress library data
    try:
        our_decompressed = lz4_block_decompress(lib_compressed)
        if our_decompressed == bytearray(test_data):
            print("SUCCESS: Our implementation successfully decompressed library compressed data")
        else:
            print(f"FAILURE: Our decompression produced incorrect output: {our_decompressed}")
    except Exception as e:
        print(f"FAILURE: Our implementation couldn't decompress library data: {str(e)}")


if __name__ == "__main__":
    print("LZ4 Block Format Analysis and Compatibility Test")
    print("------------------------------------------------")
    
    test_compatibility()