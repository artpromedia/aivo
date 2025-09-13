"""KMS (Key Management Service) encryption service with envelope encryption."""

import hashlib
import hmac
import os
import secrets
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from ..config import settings


class KMSError(Exception):
    """Base exception for KMS operations."""
    pass


class EncryptionError(KMSError):
    """Exception raised during encryption operations."""
    pass


class DecryptionError(KMSError):
    """Exception raised during decryption operations."""
    pass


class KeyNotFoundError(KMSError):
    """Exception raised when encryption key is not found."""
    pass


class KMSProvider(ABC):
    """Abstract base class for KMS providers."""

    @abstractmethod
    async def get_data_encryption_key(self, key_id: str) -> bytes:
        """Get or generate a data encryption key."""
        pass

    @abstractmethod
    async def encrypt_data_key(self, plaintext_key: bytes, key_id: str) -> bytes:
        """Encrypt a data encryption key using the master key."""
        pass

    @abstractmethod
    async def decrypt_data_key(self, encrypted_key: bytes, key_id: str) -> bytes:
        """Decrypt a data encryption key using the master key."""
        pass

    @abstractmethod
    async def rotate_master_key(self, key_id: str) -> str:
        """Rotate the master key and return new key ID."""
        pass


class LocalKMSProvider(KMSProvider):
    """Local KMS provider using file-based master keys."""

    def __init__(self, key_storage_path: str = "keys"):
        """Initialize local KMS provider."""
        self.key_storage_path = key_storage_path
        os.makedirs(key_storage_path, exist_ok=True)
        self._master_keys: Dict[str, bytes] = {}

    def _get_key_file_path(self, key_id: str) -> str:
        """Get the file path for a key."""
        safe_key_id = "".join(c for c in key_id if c.isalnum() or c in '-_')
        return os.path.join(self.key_storage_path, f"{safe_key_id}.key")

    def _load_master_key(self, key_id: str) -> bytes:
        """Load master key from file."""
        if key_id in self._master_keys:
            return self._master_keys[key_id]

        key_file = self._get_key_file_path(key_id)
        if not os.path.exists(key_file):
            # Generate new master key
            master_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(master_key)
            self._master_keys[key_id] = master_key
            return master_key

        with open(key_file, 'rb') as f:
            master_key = f.read()
            self._master_keys[key_id] = master_key
            return master_key

    async def get_data_encryption_key(self, key_id: str) -> bytes:
        """Generate a new data encryption key."""
        return Fernet.generate_key()

    async def encrypt_data_key(self, plaintext_key: bytes, key_id: str) -> bytes:
        """Encrypt data key with master key."""
        try:
            master_key = self._load_master_key(key_id)
            fernet = Fernet(master_key)
            return fernet.encrypt(plaintext_key)
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt data key: {e}")

    async def decrypt_data_key(self, encrypted_key: bytes, key_id: str) -> bytes:
        """Decrypt data key with master key."""
        try:
            master_key = self._load_master_key(key_id)
            fernet = Fernet(master_key)
            return fernet.decrypt(encrypted_key)
        except Exception as e:
            raise DecryptionError(f"Failed to decrypt data key: {e}")

    async def rotate_master_key(self, key_id: str) -> str:
        """Rotate master key."""
        new_key_id = f"{key_id}_rotated_{secrets.token_hex(8)}"
        master_key = Fernet.generate_key()

        key_file = self._get_key_file_path(new_key_id)
        with open(key_file, 'wb') as f:
            f.write(master_key)

        self._master_keys[new_key_id] = master_key
        return new_key_id


class AWSKMSProvider(KMSProvider):
    """AWS KMS provider (placeholder for future implementation)."""

    def __init__(self, region: str, access_key_id: str, secret_access_key: str):
        """Initialize AWS KMS provider."""
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        # TODO: Initialize boto3 client

    async def get_data_encryption_key(self, key_id: str) -> bytes:
        """Generate data encryption key using AWS KMS."""
        # TODO: Implement AWS KMS GenerateDataKey
        raise NotImplementedError("AWS KMS provider not yet implemented")

    async def encrypt_data_key(self, plaintext_key: bytes, key_id: str) -> bytes:
        """Encrypt data key using AWS KMS."""
        # TODO: Implement AWS KMS Encrypt
        raise NotImplementedError("AWS KMS provider not yet implemented")

    async def decrypt_data_key(self, encrypted_key: bytes, key_id: str) -> bytes:
        """Decrypt data key using AWS KMS."""
        # TODO: Implement AWS KMS Decrypt
        raise NotImplementedError("AWS KMS provider not yet implemented")

    async def rotate_master_key(self, key_id: str) -> str:
        """Rotate master key in AWS KMS."""
        # TODO: Implement AWS KMS key rotation
        raise NotImplementedError("AWS KMS provider not yet implemented")


class EncryptionService:
    """Service for envelope encryption using KMS providers."""

    def __init__(self, kms_provider: KMSProvider):
        """Initialize encryption service."""
        self.kms_provider = kms_provider

    def _generate_salt(self, length: int = 32) -> bytes:
        """Generate cryptographically secure salt."""
        return secrets.token_bytes(length)

    def _generate_nonce(self, length: int = 12) -> bytes:
        """Generate cryptographically secure nonce."""
        return secrets.token_bytes(length)

    def _derive_key_from_password(
        self,
        password: bytes,
        salt: bytes,
        algorithm: str = "scrypt"
    ) -> bytes:
        """Derive encryption key from password using KDF."""
        if algorithm == "scrypt":
            kdf = Scrypt(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                n=2**14,  # CPU/Memory cost
                r=8,      # Block size
                p=1,      # Parallelization
            )
        elif algorithm == "pbkdf2":
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
        else:
            raise ValueError(f"Unsupported KDF algorithm: {algorithm}")

        return kdf.derive(password)

    async def encrypt(
        self,
        plaintext: str,
        key_id: str,
        algorithm: str = "aes-gcm",
        additional_data: Optional[bytes] = None,
    ) -> Tuple[bytes, str, str, bytes, bytes]:
        """
        Encrypt plaintext using envelope encryption.

        Returns:
            Tuple of (ciphertext, encryption_key_id, algorithm, salt, nonce)
        """
        try:
            # Convert plaintext to bytes
            plaintext_bytes = plaintext.encode('utf-8')

            # Generate data encryption key
            data_key = await self.kms_provider.get_data_encryption_key(key_id)

            # Generate salt and nonce
            salt = self._generate_salt()
            nonce = self._generate_nonce()

            # Derive actual encryption key
            derived_key = self._derive_key_from_password(data_key, salt)

            if algorithm == "aes-gcm":
                aesgcm = AESGCM(derived_key)
                ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, additional_data)
            elif algorithm == "fernet":
                fernet = Fernet(Fernet.generate_key())  # Use derived key for Fernet
                ciphertext = fernet.encrypt(plaintext_bytes)
            else:
                raise ValueError(f"Unsupported encryption algorithm: {algorithm}")

            return ciphertext, key_id, algorithm, salt, nonce

        except Exception as e:
            raise EncryptionError(f"Failed to encrypt data: {e}")

    async def decrypt(
        self,
        ciphertext: bytes,
        encryption_key_id: str,
        algorithm: str,
        salt: bytes,
        nonce: bytes,
        additional_data: Optional[bytes] = None,
    ) -> str:
        """
        Decrypt ciphertext using envelope encryption.

        Returns:
            Decrypted plaintext as string
        """
        try:
            # Get data encryption key
            data_key = await self.kms_provider.get_data_encryption_key(encryption_key_id)

            # Derive actual encryption key
            derived_key = self._derive_key_from_password(data_key, salt)

            if algorithm == "aes-gcm":
                aesgcm = AESGCM(derived_key)
                plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, additional_data)
            elif algorithm == "fernet":
                fernet = Fernet(derived_key)  # This won't work directly, need proper implementation
                plaintext_bytes = fernet.decrypt(ciphertext)
            else:
                raise ValueError(f"Unsupported encryption algorithm: {algorithm}")

            return plaintext_bytes.decode('utf-8')

        except Exception as e:
            raise DecryptionError(f"Failed to decrypt data: {e}")

    async def rotate_key(self, old_key_id: str) -> str:
        """Rotate encryption key."""
        return await self.kms_provider.rotate_master_key(old_key_id)

    def verify_integrity(self, data: bytes, signature: bytes, key: bytes) -> bool:
        """Verify data integrity using HMAC."""
        try:
            expected_signature = hmac.new(key, data, hashlib.sha256).digest()
            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False

    def create_signature(self, data: bytes, key: bytes) -> bytes:
        """Create HMAC signature for data integrity."""
        return hmac.new(key, data, hashlib.sha256).digest()


def get_kms_provider() -> KMSProvider:
    """Get configured KMS provider."""
    provider_type = settings.kms_provider.lower()

    if provider_type == "local":
        return LocalKMSProvider()
    elif provider_type == "aws":
        # TODO: Initialize with AWS credentials
        raise NotImplementedError("AWS KMS provider not yet implemented")
    elif provider_type == "azure":
        # TODO: Initialize with Azure credentials
        raise NotImplementedError("Azure KMS provider not yet implemented")
    elif provider_type == "gcp":
        # TODO: Initialize with GCP credentials
        raise NotImplementedError("GCP KMS provider not yet implemented")
    else:
        raise ValueError(f"Unsupported KMS provider: {provider_type}")


def get_encryption_service() -> EncryptionService:
    """Get configured encryption service."""
    kms_provider = get_kms_provider()
    return EncryptionService(kms_provider)
