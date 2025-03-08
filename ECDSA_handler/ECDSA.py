

import hashlib
from typing import Optional, Tuple, Union
from dataclasses import dataclass
from ecdsa import SigningKey, VerifyingKey, NIST256p  # Changed from SECP256r1
from ecdsa.util import sigencode_string, sigdecode_string
from ecdsa.keys import BadSignatureError

@dataclass
class ECDSAConstants:
    """Shared constants between Tool and ECU for ECDSA operations."""
    # Curve parameters
    CURVE_NAME: str = "NIST P-256"  # Updated name
    SIGNATURE_SIZE: int = 64  # r and s components, 32 bytes each for P-256
    PUBLIC_KEY_SIZE: int = 65  # Uncompressed format (0x04 + x + y coordinates)
    PRIVATE_KEY_SIZE: int = 32  # 256 bits
    
    # Hash algorithm details
    HASH_NAME: str = "SHA-256"
    HASH_SIZE: int = 32  # SHA-256 produces 32-byte digests
    
    # Error codes (can be mapped to UDS NRCs if needed)
    ERR_INVALID_INPUT: int = 0x01
    ERR_SIGNATURE_FAILED: int = 0x02
    ERR_VERIFICATION_FAILED: int = 0x03
    ERR_INTERNAL: int = 0xFF

class ECDSAManager:
    """
    Manages ECDSA operations using NIST P-256 with SHA-256 hashing
    and RFC 6979 deterministic nonce generation.
    """
    
    def __init__(self):
        """Initialize the ECDSA manager with curve parameters and keys."""
        # Shared parameters (would be known to both tool and ECU)
        self.constants = ECDSAConstants()
        self.curve = NIST256p  # Changed from SECP256r1
        self.hash_function = hashlib.sha256
        
        # Private parameters (should be securely stored in production)
        self._private_key: Optional[SigningKey] = None
        self._public_key: Optional[VerifyingKey] = None
        
        # Initialize with a test key pair (for demonstration only)
        self._initialize_test_keys()

    def _initialize_test_keys(self) -> None:
        """
        Initialize a test key pair. In production, keys should be securely stored
        and loaded from a protected location (e.g., HSM, secure element).
        """
        try:
            # Example private key (32 bytes = 64 hex chars) - DO NOT USE IN PRODUCTION
            test_private_key_hex = (
                "11223344556677889900112233445566"  # First 16 bytes
                "77889900112233445566778899001122"  # Second 16 bytes
            )
            
            # Verify the length is correct before conversion
            if len(test_private_key_hex) != 64:  # 32 bytes = 64 hex chars
                raise ValueError(f"Private key must be 64 hex chars, got {len(test_private_key_hex)}")
                
            private_key_bytes = bytes.fromhex(test_private_key_hex)
            
            # Verify the byte length
            if len(private_key_bytes) != self.constants.PRIVATE_KEY_SIZE:
                raise ValueError(f"Private key must be {self.constants.PRIVATE_KEY_SIZE} bytes")
            
            # Create signing key from private key bytes
            self._private_key = SigningKey.from_string(
                private_key_bytes,
                curve=self.curve,
                hashfunc=self.hash_function
            )
            
            # Generate corresponding public key
            self._public_key = self._private_key.get_verifying_key()
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize keys: {str(e)}")
    
    def get_public_key(self) -> bytes:
        """
        Return the public key in uncompressed format (0x04 || x || y).
        """
        if not self._public_key:
            raise RuntimeError("Public key not initialized")
        
        # Get raw public key bytes (includes 0x04 prefix for uncompressed format)
        return self._public_key.to_string("uncompressed")

    def sign_message(self, message: bytearray) -> Tuple[bytearray, int]:
        """
        Sign a message using ECDSA with RFC 6979 deterministic nonce generation.
        
        Args:
            message: The message to sign as bytearray
            
        Returns:
            Tuple[bytearray, int]: (signature, status_code)
            - signature: The ECDSA signature as bytearray (r || s format)
            - status_code: 0 for success, error code otherwise
        """
        try:
            # Input validation
            if not isinstance(message, bytearray):
                print("Error: Input must be bytearray")
                return bytearray(), self.constants.ERR_INVALID_INPUT
                
            if not self._private_key:
                return bytearray(), self.constants.ERR_INTERNAL
            
            # Sign the message deterministically (RFC 6979)
            signature_bytes = self._private_key.sign_deterministic(
                bytes(message),  # Convert bytearray to bytes for signing
                hashfunc=self.hash_function,
                sigencode=sigencode_string  # Outputs raw r || s format
            )
            
            # Convert signature to bytearray
            signature = bytearray(signature_bytes)
            
            # Verify signature length
            if len(signature) != self.constants.SIGNATURE_SIZE:
                return bytearray(), self.constants.ERR_SIGNATURE_FAILED
            
            return signature, 0
            
        except Exception as e:
            print(f"Signing error: {str(e)}")
            return bytearray(), self.constants.ERR_SIGNATURE_FAILED

    def verify_signature(
        self, 
        message: bytearray,
        signature: bytearray
    ) -> Tuple[bool, int]:
        """
        Verify an ECDSA signature over a message.
        
        Args:
            message: The original message that was signed (bytearray)
            signature: The signature to verify (r || s format) (bytearray)
            
        Returns:
            Tuple[bool, int]: (is_valid, status_code)
            - is_valid: True if signature is valid, False otherwise
            - status_code: 0 for success, error code otherwise
        """
        try:
            # Input validation
            if not isinstance(message, bytearray) or not isinstance(signature, bytearray):
                print("Error: Inputs must be bytearray")
                return False, self.constants.ERR_INVALID_INPUT
                
            if len(signature) != self.constants.SIGNATURE_SIZE:
                print(f"Error: Invalid signature size: {len(signature)}")
                return False, self.constants.ERR_INVALID_INPUT
                
            if not self._public_key:
                return False, self.constants.ERR_INTERNAL
            
            # Convert bytearrays to bytes for verification
            message_bytes = bytes(message)
            signature_bytes = bytes(signature)
            
            # Verify the signature
            is_valid = self._public_key.verify(
                signature_bytes,
                message_bytes,
                hashfunc=self.hash_function,
                sigdecode=sigdecode_string  # Expects raw r || s format
            )
            
            return True, 0
            
        except BadSignatureError:
            return False, self.constants.ERR_VERIFICATION_FAILED
        except Exception as e:
            print(f"Verification error: {str(e)}")
            return False, self.constants.ERR_INTERNAL
        
    def compute_message_hash(self, message: Union[bytes, bytearray]) -> bytes:
        """
        Compute the SHA-256 hash of a message.
        Useful for debugging or comparing with other implementations.
        """
        return self.hash_function(message).digest()
    
def main():
    """
    Comprehensive example demonstrating ECDSA operations with detailed output.
    """
    print("\n" + "="*80)
    print("ECDSA (NIST P-256) Demonstration with ByteArray Input/Output")
    print("="*80)

    # Create ECDSA manager instance
    ecdsa = ECDSAManager()
    
    # 1. Get and display public key
    print("\n1. Public Key Information:")
    print("-"*50)
    public_key = ecdsa.get_public_key()
    print(f"Public Key Type:    {type(public_key)}")
    print(f"Public Key Length:  {len(public_key)} bytes")
    print(f"Public Key (hex):   {public_key.hex()}")
    
    # 2. Original Message
    print("\n2. Original Message Details:")
    print("-"*50)
    message = bytearray(b"Hello, ECDSA with NIST P-256! This is a test message to be signed.")
    print(f"Message Type:       {type(message)}")
    print(f"Message Length:     {len(message)} bytes")
    print(f"Message (ascii):    {message.decode('ascii')}")
    print(f"Message (hex):      {message.hex()}")
    
    # 3. Message Hash
    print("\n3. Message Hash (SHA-256):")
    print("-"*50)
    msg_hash = ecdsa.compute_message_hash(message)
    print(f"Hash Type:          {type(msg_hash)}")
    print(f"Hash Length:        {len(msg_hash)} bytes")
    print(f"Hash Value (hex):   {msg_hash.hex()}")
    
    # 4. Sign the message
    print("\n4. Signature Generation:")
    print("-"*50)
    signature, status = ecdsa.sign_message(message)
    if status != 0:
        print(f"ERROR: Signing failed with status: {status}")
        return
    
    print(f"Signature Type:     {type(signature)}")
    print(f"Signature Length:   {len(signature)} bytes")
    print(f"Signature (hex):    {signature.hex()}")
    print(f"  First 32 bytes (r):  {signature[:32].hex()}")
    print(f"  Last 32 bytes (s):   {signature[32:].hex()}")
    
    # 5. Verify original signature
    print("\n5. Signature Verification (Original Message):")
    print("-"*50)
    is_valid, status = ecdsa.verify_signature(message, signature)
    if status != 0:
        print(f"ERROR: Verification failed with status: {status}")
    else:
        print(f"Verification Status: {'SUCCESS' if is_valid else 'FAILED'}")
        print(f"Status Code:         {status}")

    # 6. Test with modified message
    print("\n6. Verification Test (Modified Message):")
    print("-"*50)
    modified_message = bytearray(b"Hello, ECDSA with NIST P-256! This is a MODIFIED message!")
    print(f"Modified Message:    {modified_message.decode('ascii')}")
    is_valid, status = ecdsa.verify_signature(modified_message, signature)
    print(f"Should be Invalid:   {'CORRECT (invalid)' if not is_valid else 'ERROR (valid)'}")
    print(f"Status Code:         {status}")

    # 7. Test with corrupted signature
    print("\n7. Verification Test (Corrupted Signature):")
    print("-"*50)
    corrupted_signature = signature.copy()
    corrupted_signature[0] ^= 0xFF  # Flip bits in first byte
    print(f"Original 1st byte:   0x{signature[0]:02x}")
    print(f"Corrupted 1st byte:  0x{corrupted_signature[0]:02x}")
    is_valid, status = ecdsa.verify_signature(message, corrupted_signature)
    print(f"Should be Invalid:   {'CORRECT (invalid)' if not is_valid else 'ERROR (valid)'}")
    print(f"Status Code:         {status}")

    # 8. Error handling demonstration
    print("\n8. Error Handling Examples:")
    print("-"*50)
    
    # Test with wrong input type
    print("a) Wrong Input Type Test:")
    wrong_type_message = "Not a bytearray"
    signature, status = ecdsa.sign_message(wrong_type_message)  # type: ignore
    print(f"Status Code:         {status} (should be error)")
    
    # Test with empty message
    print("\nb) Empty Message Test:")
    empty_message = bytearray()
    signature, status = ecdsa.sign_message(empty_message)
    print(f"Status Code:         {status}")
    
    # 9. Summary
    print("\n9. Test Summary:")
    print("-"*50)
    print(" Successfully demonstrated:")
    print("  • Public key generation and display")
    print("  • Message preparation and hashing")
    print("  • Signature generation (r,s components)")
    print("  • Signature verification (valid case)")
    print("  • Signature verification (invalid cases)")
    print("  • Error handling")
    
    print("\n" + "="*80)
    print("End of ECDSA Demonstration")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()