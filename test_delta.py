import sys
import os
from hex_parser.SRecordParser import DataRecord, SRecordParser
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from delta_generator.DeltaGenerator import DeltaGenerator, DeltaAlgorithm

def main():
    parser = SRecordParser()
    parser.parse_file(filename="D:\ASU\graduationProject\ISO-TP\Application_Z4_0.srec")
    old_data=parser._merged_records
    print(old_data)
    parser.parse_file(filename="D:\ASU\graduationProject\ISO-TP\Application_Z4_1.srec")
    new_data=parser._merged_records  
    print(new_data) 
    deltagenerator=DeltaGenerator(algorithm=DeltaAlgorithm.SENDING_COMPLETE_SECTOR)
    print('*'*100)
    delta_records=deltagenerator.generate_delta(old_version=old_data,new_version=new_data)
    print(delta_records)



if __name__ == "__main__":
    main()
