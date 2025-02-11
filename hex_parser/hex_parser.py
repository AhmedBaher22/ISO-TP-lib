from enum import Enum
from dataclasses import dataclass


class RecordType(Enum):
    TWO_BYTES = 2
    THREE_BYTES = 3
    FOUR_BYTES = 4


@dataclass
class DataRecord:
    record_type: RecordType
    address: str
    data: str
    data_length: int


def verify_checksum(record: str, provided_checksum: int) -> bool:
    """
    Verifies the checksum of an S-Record.
    The checksum is calculated as the one's complement of the sum of all bytes in the record (excluding 'S' and checksum itself).
    """
    byte_values = [int(record[i:i+2], 16) for i in range(2, len(record) - 3, 2)]
    sum_bytes = sum(byte_values)
    calculated_checksum = 0xFF - (sum_bytes & 0xFF)
    return calculated_checksum == provided_checksum


class SRecordParser:
    def __init__(self):
        self._records: list[DataRecord] = []  # Initialize an empty list for parsed records
        self._records_to_be_sent: list[DataRecord] = []  # Initialize an empty list for parsed records
        self._records_count = -1
        self._s1_start_address = -1
        self._s2_start_address = -1
        self._s3_start_address = -1

    def sort_records(self):
        """Sorts the records based on the address (from lowest to highest)."""
        self._records.sort(key=lambda record: int(record.address, 16))

    def process_data_record(self, record: str, record_type: RecordType, byte_count: int):
        try:
            address_start_index = 4
            address_end_index = address_start_index + record_type.value * 2
            data_length = (byte_count - 1) * 2 - record_type.value * 2
            data_end_index = address_end_index + data_length

            address = record[address_start_index:address_end_index]
            data = record[address_end_index:data_end_index]
            check_sum = int(record[data_end_index:data_end_index + 2], 16)

            if not verify_checksum(record, check_sum):
                print(f"Error in record {record} - Checksum mismatch")
                return

            data_record = DataRecord(record_type=record_type, address=address, data=data, data_length=(data_length//2))
            self._records.append(data_record)  # Store parsed record

            print(f"record: {record}\n"
                  f"byte_count: {byte_count}\n"
                  f"address: {data_record.address}\n"
                  f"data: {data_record.data}\n"
                  f"check_sum: {check_sum}")

        except Exception as e:
            print(f"Error in record {record}\n{e}")
            return


    def process_count_record(self, record: str, record_type: RecordType):
        count_start_index = 4
        count_end_index = count_start_index + record_type.value * 2

        count = int(record[count_start_index:count_end_index], 16)
        print(f"count: {count}")

        check_sum = int(record[count_end_index:count_end_index + 2], 16)

        if not verify_checksum(record, check_sum):
            print(f"Error in record {record} - Checksum mismatch")
            return

        if self._records_count == -1:
            self._records_count = count
        else:
            print(f"Error in record {record} - more than one count record")
            return



    def process_start_address_record(self, record: str, record_type: RecordType):
        try:
            address_start_index = 4
            address_end_index = address_start_index + record_type.value * 2
            address = record[address_start_index:address_end_index]
            check_sum = int(record[address_end_index:address_end_index + 2], 16)

            if not verify_checksum(record, check_sum):
                print(f"Error in record {record} - Checksum mismatch")
                return

            print(f"record: {record}\n"
                  f"address: {address}\n")

            if record_type == RecordType.TWO_BYTES:
                if self._s1_start_address == -1:
                    self._s1_start_address = address
                else:
                    print(f"Error in record {record} - more than one start address record")
            elif record_type == RecordType.THREE_BYTES:
                if self._s2_start_address == -1:
                    self._s2_start_address = address
                else:
                    print(f"Error in record {record} - more than one start address record")
            elif record_type == RecordType.FOUR_BYTES:
                if self._s3_start_address == -1:
                    self._s3_start_address = address
                else:
                    print(f"Error in record {record} - more than one start address record")

        except Exception as e:
            print(f"Error in record {record}\n{e}")
            return

    def process_record(self, record: str):
        if record[0] not in ('s', 'S'):
            print(f"Error in record {record}")
            return

        byte_count = int(record[2:4], 16)
        if byte_count <= 2:
            print(f"Error in record {record} - Invalid byte count")
            return

        match record[1]:
            case '0':
                print(f"Header {record}")
            case '1':
                self.process_data_record(record=record, byte_count=byte_count, record_type=RecordType.TWO_BYTES)
            case '2':
                self.process_data_record(record=record, byte_count=byte_count, record_type=RecordType.THREE_BYTES)
            case '3':
                self.process_data_record(record=record, byte_count=byte_count, record_type=RecordType.FOUR_BYTES)
            case '4':
                print(f"Error in record {record}")
            case '5':
                self.process_count_record(record=record, record_type=RecordType.TWO_BYTES)
            case '6':
                self.process_count_record(record=record, record_type=RecordType.THREE_BYTES)
            case '7':
                self.process_start_address_record(record=record, record_type=RecordType.FOUR_BYTES)
            case '8':
                self.process_start_address_record(record=record, record_type=RecordType.THREE_BYTES)
            case '9':
                self.process_start_address_record(record=record, record_type=RecordType.TWO_BYTES)
            case _:
                print(f"Error in record {record}")


    def parse_file(self, filename: str):
        try:
            self._records: list[DataRecord] = []  # Make sure the old file is deleted
            self._records_to_be_sent: list[DataRecord] = []  # Make sure the old file is deleted
            with open(filename, "r") as file:
                for line in file:
                    self.process_record(line.split(" ")[0].strip())

            self._merge_consecutive_records()
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")

    def _merge_consecutive_records(self, max_length: int = 4096):
        """
        Merges consecutive records whose addresses are sequential while ensuring
        that the total data length does not exceed max_length.

        :param max_length: The maximum allowed data length (in bytes) per merged record.
        """
        if not self._records:
            return

        # Access parsed records
        print("\nParsed Records:")
        for rec in self._records:
            print(rec)


        self.sort_records()  # Ensure records are sorted by address
        merged_records = []
        current_record = self._records[0]

        for next_record in self._records[1:]:
            current_address = int(current_record.address, 16)
            next_address = int(next_record.address, 16)

            # Check if the next record is consecutive
            if next_address == current_address + current_record.data_length:
                # Check if adding the next record exceeds max_length
                if current_record.data_length + next_record.data_length > max_length:
                    # Store the current merged record and start a new one
                    merged_records.append(current_record)
                    current_record = next_record
                else:
                    # Merge the record
                    current_record.data += next_record.data
                    current_record.data_length += next_record.data_length
            else:
                # Store the current merged record and start a new one
                merged_records.append(current_record)
                current_record = next_record

        # Append the last record
        merged_records.append(current_record)

        self._records = merged_records  # Update the records list

    def send_file(self):
        if not self._records:
            return


# Example usage
parser = SRecordParser()
parser.parse_file(filename="hello_world_mpc5748g.srec")
# parser.sort_records()

# Access parsed records
print("\nParsed Records:")
for rec in parser._records:
    print(rec)
