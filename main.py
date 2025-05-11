import sys
import os
from time import sleep
from typing import List

current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.IsoTpConfig import IsoTpConfig
from iso_tp_layer.IsoTp import IsoTp
from uds_layer.uds_client import UdsClient
from iso_tp_layer.Address import Address
from can_layer.can_communication import CANCommunication, CANConfiguration
from can_layer.enums import CANInterface
from can_layer.CanExceptions import CANError
from uds_layer.uds_enums import SessionType
from uds_layer.server import Server
from uds_layer.transfer_request import TransferRequest
from uds_layer.transfer_enums import EncryptionMethod, CompressionMethod, CheckSumMethod
from app_initialization import init_uds_client
from hex_parser.SRecordParser import DataRecord, SRecordParser
from delta_generator.DeltaGenerator import DeltaGenerator, DeltaAlgorithm
def handle_successful_flashing(self,ecu_number:int):
    pass
def handle_failed_flashing(self,ecu_number:int,erasing_happen:bool):
    pass
def main():
    parser = SRecordParser()
    parser2 = SRecordParser()
    parser.parse_file(filename="/home/debian/Desktop/SDVSOTA/ISO-TP-lib/old_app.srec")
    parser2.parse_file(filename="/home/debian/Desktop/SDVSOTA/ISO-TP-lib/new_app.srec")
    old_data_records=parser.get_merged_records()
    new_data_records=parser2.get_merged_records()
    deltagenerator=DeltaGenerator(algorithm=DeltaAlgorithm.SENDING_COMPLETE_SECTOR)
    # print('*'*100)
    # delta_records=deltagenerator.generate_delta(old_version=old_data_records,new_version=new_data_records)
    # print(parser._merged_records)
    # print(parser._records)
    client = init_uds_client()

    # opening session control
    # Initialize communication with an ECU
    print("\n=== Initializing Communication with ECU ===")
    ecu_address = Address(addressing_mode=0, txid=0X55, rxid=0X55)
    client.add_server(ecu_address, SessionType.PROGRAMMING)
    servers: List[Server] = client.get_servers()
    sleep(1)

    flag=True
    while flag:
        if len(servers) > 0:
            client.Flash_ECU(segments=new_data_records ,recv_DA=servers[0].can_id,
                                            encryption_method=EncryptionMethod.SEC_P_256_R1,
                                            compression_method=CompressionMethod.LZ4,
                                            checksum_required=CheckSumMethod.CRC_32,
                                            on_successfull_flashing=handle_successful_flashing,
                                            on_failing_flashing=handle_failed_flashing,
                                            flashed_ecu_number=0
                                            )
            flag=False
        sleep(1)
    # client.transfer_NEW_data_to_ecu(recv_DA=servers[0].can_id, data=[0x52, 0x55, 0x32],
    #                                 encryption_method=EncryptionMethod.NO_ENCRYPTION,
    #                                 compression_method=CompressionMethod.NO_COMPRESSION,
    #                                 memory_address=[0x22, 0x10],
    #                                 checksum_required=CheckSumMethod.CRC_16)
    # #sending read data by identifier request
    # message=servers[0].read_data_by_identifier(vin=[0x01,0x90])
    # client.send_message(servers[0].can_id,message)

    # #sending ecu reset request
    # message=servers[0].ecu_reset(reset_type=0x01)
    # client.send_message(servers[0].can_id,message)

    # #sending write data by intentifier request
    # message=servers[0].write_data_by_identifier(vin=[0x01,0x90],data=[0x55,0x26])
    # client.send_message(servers[0].can_id,message)

    while True:
        sleep(1)


if __name__ == "__main__":
    main()
