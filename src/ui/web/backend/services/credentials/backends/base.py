"""Key Management Backend Base Class"""

from abc import ABC, abstractmethod


class KeyManagementBackend(ABC):
    """Abstract backend for key management."""

    @abstractmethod
    def get_key(self, version: int) -> bytes:
        """Get encryption key by version."""
        pass

    @abstractmethod
    def get_current_version(self) -> int:
        """Get current key version."""
        pass

    @abstractmethod
    def rotate_key(self) -> int:
        """Rotate to new key version."""
        pass

    @abstractmethod
    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt data (for KMS that does server-side encryption)."""
        pass

    @abstractmethod
    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt data (for KMS that does server-side encryption)."""
        pass
