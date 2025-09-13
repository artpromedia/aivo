"""Services package initialization."""

from .encryption import (
    DecryptionError,
    EncryptionError,
    EncryptionService,
    KMSError,
    KMSProvider,
    KeyNotFoundError,
    get_encryption_service,
    get_kms_provider,
)
from .namespace import NamespaceExistsError, NamespaceService
from .secret import (
    AccessDeniedError,
    SecretExpiredError,
    SecretNotFoundError,
    SecretService,
)

__all__ = [
    # Encryption Exceptions
    "DecryptionError",
    "EncryptionError",
    "KMSError",
    "KeyNotFoundError",
    # Secret Exceptions
    "AccessDeniedError",
    "SecretExpiredError",
    "SecretNotFoundError",
    # Namespace Exceptions
    "NamespaceExistsError",
    # Classes
    "EncryptionService",
    "KMSProvider",
    "NamespaceService",
    "SecretService",
    # Functions
    "get_encryption_service",
    "get_kms_provider",
]
