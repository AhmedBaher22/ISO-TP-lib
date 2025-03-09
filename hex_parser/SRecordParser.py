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
    address: str
    data: bytearray  # Store data as bytearray
    data_length: int

    def __repr__(self):
        return (f"DataRecord(record_type={self.record_type}, "
                f"address={self.address}, "
                f"data={self.data.hex().upper()}, "  # Convert bytearray to hex string
                f"data_length={self.data_length})")



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
        self._records.sort(key=lambda record: int(record.address, 16))

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

        match record_type:
            case '0':
                # print(f"Header {record}")
                pass
            case '1':
                self._process_data_record(record=record, byte_count=byte_count, record_type=RecordType.TWO_BYTES)
            case '2':
                self._process_data_record(record=record, byte_count=byte_count, record_type=RecordType.THREE_BYTES)
            case '3':
                self._process_data_record(record=record, byte_count=byte_count, record_type=RecordType.FOUR_BYTES)
            case '5':
                self._process_count_record(record=record, record_type=RecordType.TWO_BYTES)
            case '6':
                self._process_count_record(record=record, record_type=RecordType.THREE_BYTES)
            case '7':
                self._process_start_address_record(record=record, record_type=RecordType.FOUR_BYTES)
            case '8':
                self._process_start_address_record(record=record, record_type=RecordType.THREE_BYTES)
            case '9':
                self._process_start_address_record(record=record, record_type=RecordType.TWO_BYTES)
            case _:
                raise ValueError(f"Error in record {record} - The type must be in this range [0 - 9] except 4")

    def parse_file(self, filename: str):
        try:
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


    def _merge_consecutive_records(self, max_length: int = 4096):
        """
        Merges consecutive records whose addresses are sequential while ensuring
        that the total data length does not exceed max_length.

        :param max_length: The maximum allowed data length (in bytes) per merged record.
        """
        if not self._records:
            return

        self._sort_records()  # Ensure records are sorted by address
        merged_records = []

        # Create a deep copy of the records so the original remains unchanged
        records_copy = deepcopy(self._records)

        temp_record = records_copy[0]

        for next_record in records_copy[1:]:
            current_address = int(temp_record.address, 16)
            next_address = int(next_record.address, 16)

            # Check if the next record is consecutive
            if next_address == current_address + temp_record.data_length:
                # Check if adding the next record exceeds max_length
                if temp_record.data_length + next_record.data_length > max_length:
                    # Store the current merged record and start a new one
                    merged_records.append(temp_record)
                    temp_record = deepcopy(next_record)  # Use a new copy
                else:
                    # Merge the record by creating a new object instead of modifying existing ones
                    new_data = temp_record.data + next_record.data
                    temp_record = DataRecord(
                        record_type=temp_record.record_type,
                        address=temp_record.address,
                        data=new_data,
                        data_length=temp_record.data_length + next_record.data_length
                    )
            else:
                # Store the current merged record and start a new one
                merged_records.append(temp_record)
                temp_record = deepcopy(next_record)

        # Append the last record
        merged_records.append(temp_record)

        self._merged_records = merged_records  # Store the merged records separately without modifying original

    def send_file(self):
        data1 = DataRecord(address=[0x22, 0x10], data=[0x52, 0x55, 0x32], record_type=0, data_length=0)
        data2 = DataRecord(address=[0x22, 0x10], data=[0x52, 0x55, 0x32], record_type=0, data_length=0)
        datas: List[DataRecord] = []
        datas.append(data1)
        datas.append(data2)
        return datas
