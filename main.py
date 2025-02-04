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
from app_initialization import init_uds_client

def main():
    client = init_uds_client()

    #opening session control 
    # Initialize communication with an ECU
    print("\n=== Initializing Communication with ECU ===")
    ecu_address = Address(addressing_mode=0, txid=0x33, rxid=0x33)
    client.add_server(ecu_address, SessionType.EXTENDED)
    servers: List[Server] = client.get_servers()
    sleep(1)

    #sending read data by identifier request
    message=servers[0].read_data_by_identifier(vin=[0x01,0x90])
    client.send_message(servers[0].can_id,message)

    #sending ecu reset request
    message=servers[0].ecu_reset(reset_type=0x01)
    client.send_message(servers[0].can_id,message)
    
    #sending write data by intentifier request
    message=servers[0].write_data_by_identifier(vin=[0x01,0x90],data=[0x55,0x26])
    client.send_message(servers[0].can_id,message)


    while True:
        sleep(1)





if __name__ == "__main__":
    main()
