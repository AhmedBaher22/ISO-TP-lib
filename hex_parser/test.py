# from hex_parser import SRecordParser
# Example usage
from SRecordParser import SRecordParser

parser = SRecordParser()
parser.parse_file(filename="hello_world_mpc5748g.srec")


print("\nParsed Records:")
for rec in parser._records:
    print(rec)


print("\nMerged Records:")
for rec in parser._merged_records:
    print(rec)
