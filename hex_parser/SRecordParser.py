from enum import Enum
from dataclasses import dataclass
from copy import deepcopy
import os
import sys
from typing import List

current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from logger import Logger, LogType, ProtocolType


class RecordType(Enum):
    TWO_BYTES   = 2
    THREE_BYTES = 3
    FOUR_BYTES  = 4


class ValidExtensions(Enum):
    SREC = ".srec"
    S19  = ".s19"
    S28  = ".s28"
    S37  = ".s37"
    S    = ".s"
    MOT  = ".mot"


@dataclass
class DataRecord:
    record_type: RecordType
    address: bytearray
    data: bytearray  # Store data as bytearray
    data_length: int
    # def __init__(self, address: bytearray, data: bytearray):
    #     self.record_type: RecordType
    #     self.address = address
    #     self.data = data
    #     self.data_length = len(data)
    
    def __str__(self) -> str:
        addr_int = int.from_bytes(self.address, byteorder='big')
        return f"DataRecord(Address: 0x{addr_int:08X}, Data: {self.data.hex().upper()}, Length: {self.data_length})"
    
    # def __repr__(self) -> str:
    #     return self.__str__()
    
    def __repr__(self):
        return (f"DataRecord(record_type={self.record_type}, d"
                f"address={self.address.hex().upper()}, "
                f"data={self.data.hex().upper()}, "  # Convert bytearray to hex string
                f"data_length={self.data_length})")

    def to_dict(self) -> dict:
        return {
            'record_type': self.record_type.name,  # Assumes RecordType is an Enum
            'address': self.address.hex(),
            'data': self.data.hex(),
            'data_length': self.data_length
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DataRecord':
        return cls(
            record_type=RecordType[data['record_type']],  # Convert string back to Enum
            address=bytearray.fromhex(data['address']),
            data=bytearray.fromhex(data['data']),
            data_length=data['data_length']
        )

class SRecordParser:
    # Define valid record mappings once as a class attribute
    _valid_records_by_extension = {
        ValidExtensions.SREC: {'0', '1', '2', '3', '5', '6', '7', '8', '9'},
        ValidExtensions.MOT:  {'0', '1', '2', '3', '5', '6', '7', '8', '9'},
        ValidExtensions.S:    {'0', '1', '2', '3', '5', '6', '7', '8', '9'},
        ValidExtensions.S19:  {'0', '1',           '5', '6',           '9'},
        ValidExtensions.S28:  {'0',      '2',      '5', '6',      '8'     },
        ValidExtensions.S37:  {'0',           '3', '5', '6', '7'          },
    }
    
    def __init__(self):
        self._records: list[DataRecord] = []  # Initialize an empty list for parsed records
        self._merged_records: list[DataRecord] = []  # Initialize an empty list for parsed records
        self._records_count = -1
        self._start_address = -1
        self._file_extension = None
        self._logger = Logger(ProtocolType.HEX_PARSER)
        self._logger.log_message(log_type=LogType.INITIALIZATION,
                                 message="Parser Initialized Successfully.")
        
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
            0x01580000  # End boundary for the last sector
        ]

    def get_merged_records(self):
        return self._merged_records
    
    @staticmethod
    def _verify_checksum(record: str, provided_checksum: int) -> bool:
        """
        Verifies the checksum of an S-Record.
        The checksum is calculated as the one's complement of the sum of all bytes in the record (excluding 'S' and checksum itself).
        """
        byte_values = [int(record[i:i + 2], 16) for i in range(2, len(record) - 3, 2)]
        sum_bytes = sum(byte_values)
        calculated_checksum = 0xFF - (sum_bytes & 0xFF)
        return calculated_checksum == provided_checksum

    def _sort_records(self):
        """Sorts the records based on the address (from lowest to highest)."""
        self._records.sort(key=lambda record: int.from_bytes(record.address, byteorder='big'))

    def _process_data_record(self, record: str, record_type: RecordType, byte_count: int):
        address_start_index = 4
        address_end_index = address_start_index + record_type.value * 2
        data_length = (byte_count - 1) * 2 - record_type.value * 2
        data_end_index = address_end_index + data_length

        address = record[address_start_index:address_end_index]
        data_hex_str = record[address_end_index:data_end_index]

        check_sum = int(record[data_end_index:data_end_index + 2], 16)

        if not SRecordParser._verify_checksum(record, check_sum):
            raise ValueError(f"Error in record {record} - Checksum mismatch")

        # Convert hex string to bytearray
        data = bytearray.fromhex(data_hex_str)
        address = bytearray.fromhex(address)

        data_record = DataRecord(record_type=record_type, address=address, data=data, data_length=len(data))

        self._records.append(data_record)  # Store parsed record

    def _process_count_record(self, record: str, record_type: RecordType):
        count_start_index = 4
        count_end_index = count_start_index + record_type.value * 2

        count = int(record[count_start_index:count_end_index], 16)

        check_sum = int(record[count_end_index:count_end_index + 2], 16)

        if not SRecordParser._verify_checksum(record, check_sum):
            raise ValueError(f"Error in record {record} - Checksum mismatch")

        if self._records_count == -1:
            self._records_count = count
        else:
            raise ValueError(f"Error in record {record} - more than one count record")

    def _process_start_address_record(self, record: str, record_type: RecordType):
        address_start_index = 4
        address_end_index = address_start_index + record_type.value * 2
        address = record[address_start_index:address_end_index]
        address = bytearray.fromhex(address)
        check_sum = int(record[address_end_index:address_end_index + 2], 16)

        if not SRecordParser._verify_checksum(record, check_sum):
            raise ValueError(f"Error in record {record} - Checksum mismatch")

        if self._start_address == -1:
            self._start_address = address
        else:
            raise ValueError(f"Error in record {record} - more than one start address record (Termination)")



    def _process_record(self, record: str):
        if record[0] not in ('s', 'S'):
            raise ValueError(f"Error in record {record} - Doesn't start with 'S'")

        byte_count = int(record[2:4], 16)
        if byte_count <= 2 or byte_count > 255:
            raise ValueError(f"Error in record {record} - Invalid byte count must be more than > 2 and less than 256")


        # Check if the record type is valid for the current file extension
        record_type = record[1]
        if self._file_extension not in self._valid_records_by_extension:
            raise ValueError(f"Unknown file extension {self._file_extension}")

        if record_type not in self._valid_records_by_extension[self._file_extension]:
            raise ValueError(
                f"Error in record {record} - Type S{record_type} is not allowed for {self._file_extension}")

        if record_type == '0':
            # print(f"Header {record}")
            pass
        elif record_type == '1':
            self._process_data_record(record=record, byte_count=byte_count, record_type=RecordType.TWO_BYTES)
        elif record_type == '2':
            self._process_data_record(record=record, byte_count=byte_count, record_type=RecordType.THREE_BYTES)
        elif record_type == '3':
            self._process_data_record(record=record, byte_count=byte_count, record_type=RecordType.FOUR_BYTES)
        elif record_type == '5':
            self._process_count_record(record=record, record_type=RecordType.TWO_BYTES)
        elif record_type == '6':
            self._process_count_record(record=record, record_type=RecordType.THREE_BYTES)
        elif record_type == '7':
            self._process_start_address_record(record=record, record_type=RecordType.FOUR_BYTES)
        elif record_type == '8':
            self._process_start_address_record(record=record, record_type=RecordType.THREE_BYTES)
        elif record_type == '9':
            self._process_start_address_record(record=record, record_type=RecordType.TWO_BYTES)
        else:
            raise ValueError(f"Error in record {record} - The type must be in this range [0 - 9] except 4")

    def parse_file(self, filename: str):
        try:
            self._records_count = -1
            self._start_address=-1
            # Extract file extension
            file_extension = os.path.splitext(filename)[1].lower()

            # Validate the extension using the Enum
            if file_extension not in {e.value for e in ValidExtensions}:
                self._logger.log_message(log_type=LogType.ERROR,
                                         message=f"Error: Invalid file extension. Expected one of {[e.value for e in ValidExtensions]}, got '{file_extension}'.")
                return

            # Store the validated extension
            self._file_extension = ValidExtensions(file_extension)

            self._logger.log_message(log_type=LogType.INFO,
                                     message=f"Starting parsing Hex file: {filename}.")

            self._records.clear()
            self._merged_records.clear()

            with open(filename, "r", encoding="utf-8") as file:
                for line in file:
                    self._process_record(line.split(" ")[0].strip())

            self._merge_consecutive_records()

            self._logger.log_message(log_type=LogType.ACKNOWLEDGMENT,
                                     message=f"Parsed Hex file: {filename} successfully.")
        except FileNotFoundError:
            self._logger.log_message(log_type=LogType.ERROR,
                                     message=f"Error: File '{filename}' not found.")
        except Exception as e:
            self._logger.log_message(log_type=LogType.ERROR,
                                     message=f"{e}")


    # def _merge_consecutive_records(self, block_size: int = 4096):
    #     """
    #     Merges consecutive records whose addresses are sequential while ensuring
    #     that the total data length does not exceed max_length.
    #
    #     :param block_size: The maximum allowed data length (in bytes) per merged record.
    #     """
    #     if not self._records:
    #         return
    #
    #     self._sort_records()  # Ensure records are sorted by address
    #     merged_records = []
    #
    #     # Create a deep copy of the records so the original remains unchanged
    #     records_copy = deepcopy(self._records)
    #
    #     temp_record = records_copy[0]
    #
    #     for next_record in records_copy[1:]:
    #         current_address = int.from_bytes(temp_record.address, byteorder='big')
    #         next_address = int.from_bytes(next_record.address, byteorder='big')
    #
    #         # Check if the next record is consecutive
    #         if next_address == current_address + temp_record.data_length:
    #             # Check if adding the next record exceeds max_length
    #             if temp_record.data_length + next_record.data_length > block_size:
    #                 # Store the current merged record and start a new one
    #                 merged_records.append(temp_record)
    #                 temp_record = deepcopy(next_record)  # Use a new copy
    #             else:
    #                 # Merge the record by creating a new object instead of modifying existing ones
    #                 new_data = temp_record.data + next_record.data
    #                 temp_record = DataRecord(
    #                     record_type=temp_record.record_type,
    #                     address=temp_record.address,
    #                     data=new_data,
    #                     data_length=temp_record.data_length + next_record.data_length
    #                 )
    #         else:
    #             # Store the current merged record and start a new one
    #             merged_records.append(temp_record)
    #             temp_record = deepcopy(next_record)
    #
    #     # Append the last record
    #     merged_records.append(temp_record)
    #
    #     self._merged_records = merged_records  # Store the merged records separately without modifying original


    def _merge_consecutive_records(self, block_size: int = 4096, merge_threshold: int = 80):
        """
        Merges consecutive records while ensuring alignment with block_size.
        Addresses are aligned to either (0x0, 0x4, 0x8, or 0xC).
        If a record is not aligned, it adds padding (0xFF) before the address.
        Records are merged if padding is below merge_threshold, but no record exceeds block_size.

        :param block_size: The maximum record size (in bytes).
        :param merge_threshold: The maximum padding allowed to merge two records.
        """
        if not self._records:
            return

        self._sort_records()  # Ensure records are sorted by address
        merged_records = []
        records_copy = deepcopy(self._records)

        temp_record = records_copy[0]
        current_address = int.from_bytes(temp_record.address, byteorder='big')

        # Align to 0x0, 0x4, 0x8, or 0xC
        aligned_address = (current_address // 16) * 16 + (current_address % 16 & 0xC)

        if current_address % 16 not in {0x0, 0x4, 0x8, 0xC}:
            padding_size = current_address - aligned_address
            temp_record.data = b'\xFF' * padding_size + temp_record.data
            temp_record.data_length += padding_size
            current_address = aligned_address
            temp_record.address = current_address.to_bytes(len(temp_record.address), byteorder='big')

        for next_record in records_copy[1:]:
            next_address = int.from_bytes(next_record.address, byteorder='big')
            next_aligned_address = (next_address // 16) * 16 + (next_address % 16 & 0xC)

            if next_address % 16 not in {0x0, 0x4, 0x8, 0xC}:
                padding_size = next_aligned_address - next_address
                next_record.data = b'\xFF' * padding_size + next_record.data
                next_record.data_length += padding_size
                next_address = next_aligned_address
                next_record.address = next_address.to_bytes(len(next_record.address), byteorder='big')

            # Check padding needed to merge
            padding_needed = next_address - (current_address + len(temp_record.data))

            curr_addr_int = self.bytearray_to_int(temp_record.address)
            next_addr_int = self.bytearray_to_int(next_record.address)
            curr_sector = self.get_sector(curr_addr_int)
            next_sector = self.get_sector(next_addr_int)
            if 0 <= padding_needed <= merge_threshold and (
                    len(temp_record.data) + padding_needed + len(next_record.data)) <= block_size\
                    and curr_sector == next_sector:
                temp_record.data += b'\xFF' * padding_needed + next_record.data
                temp_record.data_length += padding_needed + len(next_record.data)
            else:
                merged_records.append(temp_record)
                temp_record = deepcopy(next_record)
                current_address = next_address

        # Append the last record without forcing it to 4096 bytes
        merged_records.append(temp_record)
        self._merged_records = merged_records  # Store merged records separately


    def send_file(self):
        data1 = DataRecord(address=[0x22, 0x10], data=[0x52, 0x55, 0x32], record_type=0, data_length=0)
        data2 = DataRecord(address=[0x22, 0x10], data=[0x52, 0x55, 0x32], record_type=0, data_length=0)
        datas: List[DataRecord] = [data1, data2]
        return datas
    
    
    def get_sector(self, address: int) -> int:
        """Determine which sector an address belongs to"""
        for i in range(len(self.sector_boundaries) - 1):
            if self.sector_boundaries[i] <= address < self.sector_boundaries[i + 1]:
                return i
        return -1  # Address not in any defined sector


    def bytearray_to_int(self, addr: bytearray) -> int:
        """Convert bytearray address to integer"""
        try:
            return int.from_bytes(addr, byteorder='big')
        except Exception as e:
            self._logger.log_message(log_type=LogType.ERROR,
                                     message=f"Error converting address to integer: {e}")
            raise ValueError(f"Invalid address format: {addr}")
