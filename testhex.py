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
from ECDSA_handler.ECDSA import ECDSAManager, ECDSAConstants

def main():
    parser = SRecordParser()
    parser.parse_file(filename="test-file.s19")
    print(parser._merged_records)
    print(parser._records)
    segments:DataRecord=[]
    segments=parser.get_record()

    alldata = bytearray()
    for x in segments:
        alldata.extend(x.data)
    print(alldata)
    print(type(alldata))
    # Create ECDSA manager instance
    ecdsa = ECDSAManager()
    
    
    
    

    signature, status = ecdsa.sign_message(bytearray(alldata))


    msg=f"Signature Type:     {type(signature)}"
    print(msg)
    msg=f"Signature Length:   {len(signature)} bytes"
    print(msg)
    msg=f"Signature (hex):    {signature.hex()}"
    print(msg)      
    msg=f"  First 32 bytes (r):  {signature[:32].hex()}"
    print(msg)       
    msg=f"  Last 32 bytes (s):   {signature[32:].hex()}"
    print(msg)
    

main()
   

