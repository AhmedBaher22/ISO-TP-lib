import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from logger import Logger, LogType, ProtocolType
from hex_parser.SRecordParser import SRecordParser

parser = SRecordParser()
parser.parse_file(filename="hello_world_mpc5748g.srec")

logger = Logger(ProtocolType.HEX_PARSER)


# print("\nParsed Records:")
# for rec in parser._records:
#     print(rec)


# print("\nMerged Records:")
logger.log_message(log_type=LogType.DEBUG,
                   message=f"START ")
for rec in parser._merged_records[:5]:
    logger.log_message(log_type=LogType.DEBUG,
                       message=f"{rec}")
