"""
Encryption module for AES encryption at rest.
Provides secure file encryption and key management for compliance exports.
"""

import base64
import os
import secrets
from pathlib import Path
from typing import Optional, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


class EncryptionManager:
    """Manages AES encryption for compliance export files."""

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption manager.
        
        Args:
            master_key: Master key for key encryption. If None, uses environment variable.
        """
        self.master_key = (
            master_key or os.getenv("COMPLIANCE_MASTER_KEY") or self._generate_master_key()
        )

    def _generate_master_key(self) -> str:
        """Generate a new master key."""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

    def generate_file_key(self) -> Tuple[str, bytes]:
        """
        Generate a new file encryption key.
        
        Returns:
            Tuple of (key_id, encrypted_key_data)
        """
        # Generate random key ID
        key_id = secrets.token_urlsafe(32)
        
        # Generate file encryption key
        file_key = Fernet.generate_key()
        
        # Generate salt for key encryption
        salt = secrets.token_bytes(32)
        
        # Derive key encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP recommended minimum
        )
        key_encryption_key = base64.urlsafe_b64encode(
            kdf.derive(self.master_key.encode())
        )
        
        # Encrypt the file key
        fernet = Fernet(key_encryption_key)
        encrypted_key = fernet.encrypt(file_key)
        
        # Combine salt and encrypted key
        key_data = salt + encrypted_key
        
        return key_id, key_data

    def decrypt_file_key(self, key_data: bytes) -> bytes:
        """
        Decrypt a file encryption key.
        
        Args:
            key_data: Combined salt and encrypted key data
            
        Returns:
            Decrypted file encryption key
        """
        # Split salt and encrypted key
        salt = key_data[:32]
        encrypted_key = key_data[32:]
        
        # Derive key encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key_encryption_key = base64.urlsafe_b64encode(
            kdf.derive(self.master_key.encode())
        )
        
        # Decrypt the file key
        fernet = Fernet(key_encryption_key)
        file_key = fernet.decrypt(encrypted_key)
        
        return file_key

    def encrypt_file(
        self, 
        input_path: Path, 
        output_path: Path, 
        key_data: bytes
    ) -> int:
        """
        Encrypt a file using AES encryption.
        
        Args:
            input_path: Path to input file
            output_path: Path to encrypted output file
            key_data: Encrypted key data from generate_file_key()
            
        Returns:
            Size of encrypted file in bytes
        """
        # Decrypt the file key
        file_key = self.decrypt_file_key(key_data)
        fernet = Fernet(file_key)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read and encrypt file
        with open(input_path, "rb") as infile:
            file_data = infile.read()
            
        encrypted_data = fernet.encrypt(file_data)
        
        # Write encrypted file
        with open(output_path, "wb") as outfile:
            outfile.write(encrypted_data)
            
        return len(encrypted_data)

    def decrypt_file(
        self, 
        input_path: Path, 
        output_path: Path, 
        key_data: bytes
    ) -> int:
        """
        Decrypt a file using AES encryption.
        
        Args:
            input_path: Path to encrypted input file
            output_path: Path to decrypted output file
            key_data: Encrypted key data
            
        Returns:
            Size of decrypted file in bytes
        """
        # Decrypt the file key
        file_key = self.decrypt_file_key(key_data)
        fernet = Fernet(file_key)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read and decrypt file
        with open(input_path, "rb") as infile:
            encrypted_data = infile.read()
            
        decrypted_data = fernet.decrypt(encrypted_data)
        
        # Write decrypted file
        with open(output_path, "wb") as outfile:
            outfile.write(decrypted_data)
            
        return len(decrypted_data)

    def encrypt_text(self, text: str, key_data: bytes) -> str:
        """
        Encrypt text data.
        
        Args:
            text: Text to encrypt
            key_data: Encrypted key data
            
        Returns:
            Base64-encoded encrypted text
        """
        file_key = self.decrypt_file_key(key_data)
        fernet = Fernet(file_key)
        encrypted_bytes = fernet.encrypt(text.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_bytes).decode()

    def decrypt_text(self, encrypted_text: str, key_data: bytes) -> str:
        """
        Decrypt text data.
        
        Args:
            encrypted_text: Base64-encoded encrypted text
            key_data: Encrypted key data
            
        Returns:
            Decrypted text
        """
        file_key = self.decrypt_file_key(key_data)
        fernet = Fernet(file_key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')

    def secure_delete(self, file_path: Path) -> bool:
        """
        Securely delete a file by overwriting with random data.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not file_path.exists():
                return True
                
            # Get file size
            file_size = file_path.stat().st_size
            
            # Overwrite with random data (3 passes)
            with open(file_path, "r+b") as f:
                for _ in range(3):
                    f.seek(0)
                    f.write(secrets.token_bytes(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Remove the file
            file_path.unlink()
            return True
            
        except Exception:
            return False

    def validate_encryption(self, file_path: Path, key_data: bytes) -> bool:
        """
        Validate that a file can be successfully decrypted.
        
        Args:
            file_path: Path to encrypted file
            key_data: Encrypted key data
            
        Returns:
            True if file can be decrypted, False otherwise
        """
        try:
            file_key = self.decrypt_file_key(key_data)
            fernet = Fernet(file_key)
            
            # Read a small portion of the file
            with open(file_path, "rb") as f:
                encrypted_data = f.read(1024)  # Read first 1KB
                
            # Try to decrypt
            fernet.decrypt(encrypted_data)
            return True
            
        except Exception:
            return False


# Global encryption manager instance
encryption_manager = EncryptionManager()
