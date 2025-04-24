from typing import List, Tuple, Set, Dict, Optional
import logging
from enum import Enum, auto

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataRecord:
    def __init__(self, address: bytearray, data: bytearray):
        self.address = address
        self.data = data
        self.data_length = len(data)
    
    def __str__(self) -> str:
        addr_int = int.from_bytes(self.address, byteorder='big')
        return f"DataRecord(Address: 0x{addr_int:08X}, Data: {self.data.hex().upper()}, Length: {self.data_length})"
    
    def __repr__(self) -> str:
        return self.__str__()

class DeltaAlgorithm(Enum):
    """Enum for different delta generation algorithms"""
    SENDING_COMPLETE_SECTOR = auto()
    # Future algorithms can be added here
    # INCREMENTAL_DELTA = auto()
    # BINARY_DIFF = auto()

class DeltaGenerator:
    def __init__(
        self, 
        algorithm: DeltaAlgorithm = DeltaAlgorithm.SENDING_COMPLETE_SECTOR,
        sector_boundaries: Optional[List[int]] = None,
        sector_size: int = 0x40000  # 256KB default
    ):
        """
        Initialize the Delta Generator.
        
        Args:
            algorithm: The algorithm to use for delta generation
            sector_boundaries: List of sector start addresses, default is for the standard flash layout
            sector_size: Size of each sector in bytes, default is 256KB (0x40000)
        """
        self.algorithm = algorithm
        self.sector_size = sector_size
        
        # Default sector boundaries if none provided
        if sector_boundaries is None:
            self.sector_boundaries = [
                0x01000000,  # Start Address of 256KB Code Flash Block 0
                0x01040000,  # Start Address of 256KB Code Flash Block 1
                0x01080000,  # Start Address of 256KB Code Flash Block 2
                0x010C0000,  # Start Address of 256KB Code Flash Block 3
                0x01100000,  # Start Address of 256KB Code Flash Block 4
                0x01140000,  # Start Address of 256KB Code Flash Block 5
                0x01180000,  # Start Address of 256KB Code Flash Block 6
                0x011C0000,  # Start Address of 256KB Code Flash Block 7
                0x01200000,  # Start Address of 256KB Code Flash Block 8
                0x01240000,  # Start Address of 256KB Code Flash Block 9
                0x01280000,  # Start Address of 256KB Code Flash Block 10
                0x012C0000,  # Start Address of 256KB Code Flash Block 11
                0x01300000,  # Start Address of 256KB Code Flash Block 12
                0x01340000,  # Start Address of 256KB Code Flash Block 13
                0x01380000,  # Start Address of 256KB Code Flash Block 14
                0x013C0000,  # Start Address of 256KB Code Flash Block 15
                0x01400000,  # Start Address of 256KB Code Flash Block 16
                0x01440000,  # Start Address of 256KB Code Flash Block 17
                0x01480000,  # Start Address of 256KB Code Flash Block 18
                0x014C0000,  # Start Address of 256KB Code Flash Block 19
                0x01500000,  # Start Address of 256KB Code Flash Block 20
                0x01540000,  # Start Address of 256KB Code Flash Block 21
                0x01580000   # End boundary for the last sector
            ]
        else:
            # Make sure we have a proper end boundary
            self.sector_boundaries = list(sector_boundaries)
            if len(self.sector_boundaries) > 0:
                last_sector_start = self.sector_boundaries[-1]
                self.sector_boundaries.append(last_sector_start + self.sector_size)
                
        logger.info(f"Delta Generator initialized with algorithm: {self.algorithm.name}")

    def bytearray_to_int(self, addr: bytearray) -> int:
        """Convert bytearray address to integer"""
        try:
            return int.from_bytes(addr, byteorder='big')
        except Exception as e:
            logger.error(f"Error converting address to integer: {e}")
            raise ValueError(f"Invalid address format: {addr}")

    def get_sector(self, address: int) -> int:
        """Determine which sector an address belongs to"""
        for i in range(len(self.sector_boundaries) - 1):
            if self.sector_boundaries[i] <= address < self.sector_boundaries[i + 1]:
                return i
        return -1  # Address not in any defined sector

    def validate_input(self, old_version: List[DataRecord], new_version: List[DataRecord]) -> None:
        """Validate input data records"""
        if not isinstance(old_version, list) or not isinstance(new_version, list):
            raise TypeError("Both old_version and new_version must be lists of DataRecord objects")
        
        for i, record_list in enumerate([old_version, new_version]):
            version_name = "old_version" if i == 0 else "new_version"
            for j, record in enumerate(record_list):
                if not isinstance(record, DataRecord):
                    raise TypeError(f"Item at index {j} in {version_name} is not a DataRecord object")
                
                # Check if address is valid
                try:
                    addr_int = self.bytearray_to_int(record.address)
                    if self.get_sector(addr_int) == -1:
                        logger.warning(f"Address 0x{addr_int:08X} in {version_name} is not within any defined sector")
                except Exception as e:
                    raise ValueError(f"Invalid address in {version_name} at index {j}: {e}")

    def binary_search(self, addresses: List[int], target: int) -> int:
        """
        Perform binary search on sorted addresses.
        Returns: index if found, -1 if not found
        """
        left, right = 0, len(addresses) - 1
        
        while left <= right:
            mid = (left + right) // 2
            if addresses[mid] == target:
                return mid
            elif addresses[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        
        return -1  # Not found

    def generate_delta(self, old_version: List[DataRecord], new_version: List[DataRecord]) -> List[DataRecord]:
        """
        Generates delta between two versions of hex code based on sector changes.
        
        Args:
            old_version: List of DataRecord objects representing the old code
            new_version: List of DataRecord objects representing the new code
            
        Returns:
            List of DataRecord objects representing the delta (changes) between versions
        """
        try:
            # Validate input
            self.validate_input(old_version, new_version)
            
            # Choose the appropriate algorithm
            if self.algorithm == DeltaAlgorithm.SENDING_COMPLETE_SECTOR:
                return self._generate_delta_complete_sector(old_version, new_version)
            else:
                # Future algorithms will be added here
                logger.warning(f"Unknown algorithm {self.algorithm}, defaulting to SENDING_COMPLETE_SECTOR")
                return self._generate_delta_complete_sector(old_version, new_version)
                
        except Exception as e:
            logger.error(f"Error generating delta: {e}")
            raise

    def _generate_delta_complete_sector(self, old_version: List[DataRecord], new_version: List[DataRecord]) -> List[DataRecord]:
        """
        Implementation of the SENDING_COMPLETE_SECTOR algorithm.
        Sends the entire sector when any change is detected.
        """
        # Convert DataRecord lists to dictionaries for efficient access
        old_dict = {self.bytearray_to_int(record.address): record for record in old_version}
        new_dict = {self.bytearray_to_int(record.address): record for record in new_version}
        
        # Create sorted lists of addresses for optimized searching
        old_addresses = sorted(old_dict.keys())
        new_addresses = sorted(new_dict.keys())
        
        # Pre-calculate sector numbers for all addresses to avoid redundant computation
        old_addr_sectors = {addr: self.get_sector(addr) for addr in old_addresses}
        new_addr_sectors = {addr: self.get_sector(addr) for addr in new_addresses}
        
        # Set to track sectors that need to be updated
        sectors_to_update = set()
        
        # Step 1: Check for addresses in new version that don't exist in old version
        # Using optimized search
        for addr in new_addresses:
            # Skip if this address's sector is already marked for update
            sector = new_addr_sectors.get(addr, -1)
            if sector == -1 or sector in sectors_to_update:
                continue
                
            # Use binary search instead of 'in' operator
            if self.binary_search(old_addresses, addr) == -1:
                sectors_to_update.add(sector)
                logger.info(f"New address 0x{addr:08X} detected in sector {sector}")
        
        # Step 2: Check for addresses in old version that don't exist in new version
        # Using optimized search
        for addr in old_addresses:
            # Skip if this address's sector is already marked for update
            sector = old_addr_sectors.get(addr, -1)
            if sector == -1 or sector in sectors_to_update:
                continue
                
            # Use binary search instead of 'in' operator
            if self.binary_search(new_addresses, addr) == -1:
                sectors_to_update.add(sector)
                logger.info(f"Address 0x{addr:08X} removed in sector {sector}")
        
        # Step 3: Check for data differences in addresses that exist in both versions
        # Improved approach: Find the intersection of addresses and compare the data
        for addr in old_addresses:
            # Skip if this address's sector is already marked for update
            sector = old_addr_sectors.get(addr, -1)
            if sector == -1 or sector in sectors_to_update:
                continue
            
            # Check if this address exists in new version (using binary search)
            if self.binary_search(new_addresses, addr) != -1:
                # Address exists in both versions, compare data
                if old_dict[addr].data != new_dict[addr].data:
                    sectors_to_update.add(sector)
                    logger.info(f"Data changed at address 0x{addr:08X} in sector {sector}")
        
        # Prepare the delta records
        delta_records = []
        
        # For each sector that needs updating, include all records from that sector
        sectors_to_update = sorted(sectors_to_update)
        for sector in sectors_to_update:
            sector_start = self.sector_boundaries[sector]
            sector_end = self.sector_boundaries[sector + 1]
            
            logger.info(f"Updating sector {sector} (0x{sector_start:08X} - 0x{sector_end:08X})")
            
            # Add all records from the new version that belong to this sector
            sector_records = []
            for addr, record in new_dict.items():
                if sector_start <= addr < sector_end:
                    sector_records.append(record)
            
            logger.info(f"Added {len(sector_records)} records from sector {sector}")
            delta_records.extend(sector_records)
        
        return delta_records

def test_delta_generator():
    """Test the delta generator with various scenarios and configurations"""
    # Test with default settings
    print("\nTest with default settings:")
    generator = DeltaGenerator()
    
    # Scenario 1: Change in one sector
    print("\nScenario 1: Change in one sector")
    old_version = [
        DataRecord(bytearray.fromhex('01000100'), bytearray.fromhex('AABBCCDD')),
        DataRecord(bytearray.fromhex('01000200'), bytearray.fromhex('11223344'))
    ]
    new_version = [
        DataRecord(bytearray.fromhex('01000100'), bytearray.fromhex('AABBCCEE')),  # Changed
        DataRecord(bytearray.fromhex('01000200'), bytearray.fromhex('11223344'))   # Same
    ]
    delta = generator.generate_delta(old_version, new_version)
    print(f"Delta contains {len(delta)} records")
    for record in delta:
        addr = generator.bytearray_to_int(record.address)
        print(f"Address: 0x{addr:08X}, Data: {record.data.hex().upper()}")
    
    # Test with custom sector boundaries
    print("\nTest with custom sector boundaries:")
    custom_boundaries = [0x02000000, 0x02010000, 0x02020000]  # 64KB sectors
    custom_generator = DeltaGenerator(
        algorithm=DeltaAlgorithm.SENDING_COMPLETE_SECTOR,
        sector_boundaries=custom_boundaries,
        sector_size=0x10000  # 64KB
    )
    
    # Scenario with custom boundaries
    print("\nScenario with custom boundaries")
    old_version = [
        DataRecord(bytearray.fromhex('02000100'), bytearray.fromhex('AABBCCDD')),
        DataRecord(bytearray.fromhex('02010100'), bytearray.fromhex('11223344'))
    ]
    new_version = [
        DataRecord(bytearray.fromhex('02000100'), bytearray.fromhex('AABBCCEE')),  # Changed
        DataRecord(bytearray.fromhex('02010100'), bytearray.fromhex('11223344'))   # Same
    ]
    delta = custom_generator.generate_delta(old_version, new_version)
    print(f"Delta contains {len(delta)} records")
    for record in delta:
        addr = custom_generator.bytearray_to_int(record.address)
        print(f"Address: 0x{addr:08X}, Data: {record.data.hex().upper()}")
    
    # Test optimization with large data sets
    print("\nTesting optimization with larger data sets:")
    large_old_version = []
    large_new_version = []
    
    # Create records across multiple sectors
    for i in range(10):
        base_addr = 0x01000000 + (i * 0x1000)
        large_old_version.append(DataRecord(
            bytearray.fromhex(f'{base_addr:08X}'), 
            bytearray.fromhex('AA' * 16)
        ))
        
        # Make the new version slightly different
        large_new_version.append(DataRecord(
            bytearray.fromhex(f'{base_addr:08X}'), 
            bytearray.fromhex('AA' * 16)
        ))
    
    # Change one record to trigger sector update
    large_new_version[5].data = bytearray.fromhex('BB' * 16)
    
    # Add a record that exists only in new version
    new_only_addr = 0x01100100
    large_new_version.append(DataRecord(
        bytearray.fromhex(f'{new_only_addr:08X}'),
        bytearray.fromhex('CC' * 16)
    ))
    
    import time
    start_time = time.time()
    delta = generator.generate_delta(large_old_version, large_new_version)
    end_time = time.time()
    
    print(f"Delta generation took {end_time - start_time:.6f} seconds")
    print(f"Delta contains {len(delta)} records")
    
    # Verify sectors being updated
    updated_sectors = set()
    for record in delta:
        addr = generator.bytearray_to_int(record.address)
        sector = generator.get_sector(addr)
        updated_sectors.add(sector)
    
    print(f"Updated sectors: {sorted(updated_sectors)}")

if __name__ == "__main__":
    test_delta_generator()