import json
from typing import Dict, Any

class Protocol:
    # Message types
    HANDSHAKE = "HANDSHAKE"
    UPDATE_CHECK = "UPDATE_CHECK"
    UPDATE_RESPONSE = "UPDATE_RESPONSE"
    DOWNLOAD_REQUEST = "DOWNLOAD_REQUEST"
    DOWNLOAD_START = "DOWNLOAD_START"
    FILE_CHUNK = "FILE_CHUNK"
    DOWNLOAD_COMPLETE = "DOWNLOAD_COMPLETE"
    ERROR = "ERROR"

    @staticmethod
    def create_message(msg_type: str, payload: Dict) -> bytes:
        """Create a formatted message to send over socket"""
        message = {
            "type": msg_type,
            "payload": payload
        }
        # Convert to JSON and add message length prefix
        json_msg = json.dumps(message)
        msg_length = len(json_msg)
        return f"{msg_length:010d}{json_msg}".encode()

    @staticmethod
    def parse_message(data: bytes) -> Dict[str, Any]:
        """Parse received message"""
        try:
            return json.loads(data.decode())
        except json.JSONDecodeError:
            return None

    @staticmethod
    def create_handshake_response(success: bool, message: str) -> bytes:
        return Protocol.create_message(Protocol.HANDSHAKE, {
            "success": success,
            "message": message
        })

    @staticmethod
    def create_update_response(updates_needed: Dict[str, str]) -> bytes:
        return Protocol.create_message(Protocol.UPDATE_RESPONSE, {
            "updates_needed": updates_needed
        })

    @staticmethod
    def create_error_message(error_code: int, error_message: str) -> bytes:
        return Protocol.create_message(Protocol.ERROR, {
            "code": error_code,
            "message": error_message
        })