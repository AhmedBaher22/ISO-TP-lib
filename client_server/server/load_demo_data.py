"""
MongoDB Demo Data Loader

This script loads sample data into the MongoDB collections for the automotive firmware database.
"""

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import os
import json
from datetime import datetime
from typing import Dict, List

# MongoDB connection
uri = "mongodb+srv://ahmedbaher382001:VMv7y5NvzU0R3aFA@cluster0.ggbavh1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['automotive_firmware_db']

# Collections
car_types_collection = db['car_types']
ecus_collection = db['ecus']
versions_collection = db['versions']
requests_collection = db['requests']
download_requests_collection = db['download_requests']

def clear_collections():
    """Clear all collections before loading demo data"""
    print("Clearing existing collections...")
    car_types_collection.delete_many({})
    ecus_collection.delete_many({})
    versions_collection.delete_many({})
    requests_collection.delete_many({})
    download_requests_collection.delete_many({})

def load_versions():
    """Load version data and return a mapping of version IDs to ObjectIDs"""
    print("Loading version data...")
    version_mapping = {}
    
    versions_data = [
        {
            "version_number": "1.0.0",
            "compatible_car_types": ["ModelX", "ModelY"],
            "hex_file_path": "hex_files/hello.srec"
        },
        {
            "version_number": "1.1.0",
            "compatible_car_types": ["ModelX", "ModelY"],
            "hex_file_path": "hex_files/ECM_1_1_0.hex"
        },
        {
            "version_number": "1.2.0",
            "compatible_car_types": ["ModelX", "ModelY"],
            "hex_file_path": "hex_files/ECM_1_2_0.hex"
        },
        {
            "version_number": "1.0.0",
            "compatible_car_types": ["ModelX", "ModelY"],
            "hex_file_path": "hex_files/TCM_1_0_0.hex"
        },
        {
            "version_number": "1.1.0",
            "compatible_car_types": ["ModelX", "ModelY"],
            "hex_file_path": "hex_files/TCM_1_1_0.hex"
        },
        {
            "version_number": "1.0.0",
            "compatible_car_types": ["ModelX"],
            "hex_file_path": "hex_files/BCM_1_0_0.hex"
        },
        {
            "version_number": "1.1.0",
            "compatible_car_types": ["ModelX"],
            "hex_file_path": "hex_files/hello.srec"
        },
        {
            "version_number": "1.0.0",
            "compatible_car_types": ["ModelY"],
            "hex_file_path": "hex_files/BMS_1_0_0.hex"
        },
        {
            "version_number": "1.1.0",
            "compatible_car_types": ["ModelY"],
            "hex_file_path": "hex_files/hello.srec"
        },
        {
            "version_number": "1.2.0",
            "compatible_car_types": ["ModelY"],
            "hex_file_path": "hex_files/BMS_1_2_0.hex"
        }
    ]
    
    # Map the IDs from the provided data to the versions
    version_ids = ["ECM_V1", "ECM_V2", "ECM_V3", "TCM_V1", "TCM_V2", 
                   "BCM_V1", "BCM_V2", "BMS_V1", "BMS_V2", "BMS_V3"]
    
    for i, (version_id, version_data) in enumerate(zip(version_ids, versions_data)):
        # Create a MongoDB ObjectId for each version
        object_id = ObjectId()
        version_mapping[version_id] = object_id
        
        # Add the ObjectId and original ID for reference
        version_data["_id"] = object_id
        version_data["original_id"] = version_id
        
        # Insert into MongoDB
        versions_collection.insert_one(version_data)
        print(f"  Inserted version: {version_id} -> {object_id}")
    
    return version_mapping

def load_ecus(version_mapping):
    """Load ECU data and return a mapping of ECU IDs to ObjectIDs"""
    print("Loading ECU data...")
    ecu_mapping = {}
    
    ecus_data = [
        {
            "name": "Engine_Control_Module",
            "model_number": "ECM_2023",
            "version_ids": ["ECM_V1", "ECM_V2", "ECM_V3"]
        },
        {
            "name": "Transmission_Control_Module",
            "model_number": "TCM_2023",
            "version_ids": ["TCM_V1", "TCM_V2"]
        },
        {
            "name": "Brake_Control_Module",
            "model_number": "BCM_2023",
            "version_ids": ["BCM_V1", "BCM_V2"]
        },
        {
            "name": "Battery_Management_System",
            "model_number": "BMS_2023",
            "version_ids": ["BMS_V1", "BMS_V2", "BMS_V3"]
        }
    ]
    
    # Map the IDs from the provided data to the ECUs
    ecu_ids = ["ECU001", "ECU002", "ECU003", "ECU004"]
    
    for i, (ecu_id, ecu_data) in enumerate(zip(ecu_ids, ecus_data)):
        # Create a MongoDB ObjectId for each ECU
        object_id = ObjectId()
        ecu_mapping[ecu_id] = object_id
        
        # Convert version_ids to ObjectIds using the mapping
        ecu_data["version_ids"] = [version_mapping[v_id] for v_id in ecu_data["version_ids"]]
        
        # Add the ObjectId and original ID for reference
        ecu_data["_id"] = object_id
        ecu_data["original_id"] = ecu_id
        
        # Insert into MongoDB
        ecus_collection.insert_one(ecu_data)
        print(f"  Inserted ECU: {ecu_id} -> {object_id}")
    
    return ecu_mapping

def load_car_types(ecu_mapping):
    """Load car type data"""
    print("Loading car type data...")
    
    car_types_data = [
        {
            "name": "ModelX",
            "model_number": "MX2023",
            "manufactured_count": 100,
            "car_ids": [
                "MX2023-001",
                "MX2023-002",
                "MX2023-003",
                "MX2023-004",
                "MX2023-005"
            ],
            "ecu_ids": ["ECU001", "ECU002", "ECU003"]
        },
        {
            "name": "ModelY",
            "model_number": "MY2023",
            "manufactured_count": 50,
            "car_ids": [
                "MY2023-001",
                "MY2023-002",
                "MY2023-003"
            ],
            "ecu_ids": ["ECU001", "ECU002", "ECU004"]
        }
    ]
    
    for car_type_data in car_types_data:
        # Convert ecu_ids to ObjectIds using the mapping
        car_type_data["ecu_ids"] = [ecu_mapping[e_id] for e_id in car_type_data["ecu_ids"]]
        
        # Insert into MongoDB
        result = car_types_collection.insert_one(car_type_data)
        print(f"  Inserted car type: {car_type_data['name']} -> {result.inserted_id}")

def load_sample_requests():
    """Load sample request data"""
    print("Loading sample requests...")
    
    # Sample service requests
    requests_data = [
        {
            "timestamp": datetime.now(),
            "car_type": "ModelX",
            "car_id": "MX2023-001",
            "ip_address": "192.168.1.100",
            "port": 8080,
            "service_type": "CHECK_UPDATES",
            "metadata": {
                "Engine_Control_Module": "1.0.0",
                "Transmission_Control_Module": "1.0.0",
                "Brake_Control_Module": "1.0.0"
            },
            "status": "COMPLETED"
        },
        {
            "timestamp": datetime.now(),
            "car_type": "ModelY",
            "car_id": "MY2023-001",
            "ip_address": "192.168.1.200",
            "port": 8080,
            "service_type": "CHECK_UPDATES",
            "metadata": {
                "Engine_Control_Module": "1.0.0",
                "Transmission_Control_Module": "1.0.0",
                "Battery_Management_System": "1.0.0"
            },
            "status": "COMPLETED"
        }
    ]
    
    for request_data in requests_data:
        result = requests_collection.insert_one(request_data)
        print(f"  Inserted request for car: {request_data['car_id']} -> {result.inserted_id}")
    
    # Sample download requests
    download_requests_data = [
        {
            "timestamp": datetime.now(),
            "car_type": "ModelX",
            "car_id": "MX2023-001",
            "ip_address": "192.168.1.100",
            "port": 8080,
            "required_versions": {
                "Engine_Control_Module": "1.2.0",
                "Transmission_Control_Module": "1.1.0"
            },
            "old_versions": {
                "Engine_Control_Module": "1.0.0",
                "Transmission_Control_Module": "1.0.0"
            },
            "status": "COMPLETED",
            "total_size": 512000,
            "transferred_size": 512000,
            "active_transfers": {
                "Engine_Control_Module": False,
                "Transmission_Control_Module": False
            }
        },
        {
            "timestamp": datetime.now(),
            "car_type": "ModelY",
            "car_id": "MY2023-002",
            "ip_address": "192.168.1.201",
            "port": 8080,
            "required_versions": {
                "Battery_Management_System": "1.2.0"
            },
            "old_versions": {
                "Battery_Management_System": "1.0.0"
            },
            "status": "IN_PROGRESS",
            "total_size": 256000,
            "transferred_size": 128000,
            "active_transfers": {
                "Battery_Management_System": True
            }
        }
    ]
    
    for request_data in download_requests_data:
        result = download_requests_collection.insert_one(request_data)
        print(f"  Inserted download request for car: {request_data['car_id']} -> {result.inserted_id}")

def ensure_hex_file_directory():
    """Create hex files directory and dummy files if needed"""
    print("Ensuring hex files directory and dummy files exist...")
    hex_dir = "hex_files"
    
    if not os.path.exists(hex_dir):
        os.makedirs(hex_dir)
        print(f"  Created directory: {hex_dir}")
    
    # Create dummy hex files
    hex_files = [
        "hello.srec",
        "ECM_1_1_0.hex",
        "ECM_1_2_0.hex",
        "TCM_1_0_0.hex",
        "TCM_1_1_0.hex",
        "BCM_1_0_0.hex",
        "BMS_1_0_0.hex",
        "BMS_1_2_0.hex"
    ]
    
    for file_name in hex_files:
        file_path = os.path.join(hex_dir, file_name)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(f"Dummy hex content for {file_name}")
            print(f"  Created dummy file: {file_path}")

def main():
    """Main function to load all demo data"""
    try:
        # Test connection
        client.admin.command('ping')
        print("Connected successfully to MongoDB!")
        
        # Clear existing data
        clear_collections()
        
        # Create hex files directory and dummy files
        ensure_hex_file_directory()
        
        # Load data with proper references
        version_mapping = load_versions()
        ecu_mapping = load_ecus(version_mapping)
        load_car_types(ecu_mapping)
        load_sample_requests()
        
        print("\nDemo data loaded successfully!")
        
        # Verify the data
        print("\nVerifying data counts:")
        print(f"Car Types: {car_types_collection.count_documents({})}")
        print(f"ECUs: {ecus_collection.count_documents({})}")
        print(f"Versions: {versions_collection.count_documents({})}")
        print(f"Requests: {requests_collection.count_documents({})}")
        print(f"Download Requests: {download_requests_collection.count_documents({})}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the connection
        client.close()
        print("\nMongoDB connection closed")

if __name__ == "__main__":
    main()