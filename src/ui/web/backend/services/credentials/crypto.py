"""Credential encryption and decryption utilities."""

import base64
import hashlib
import hmac
import logging

from services.credentials.encryption import EncryptionKey
from services.credentials.backends import LocalKeyBackend

logger = logging.getLogger(__name__)


class CredentialCryptoMixin:
    """Mixin providing encryption/decryption for credentials."""

    @classmethod
    def _encrypt(cls, value: str, key_version: int) -> str:
        """
        Encrypt value using the configured backend.

        Uses AES-256-GCM or backend-specific encryption (Vault/KMS).
        """
        try:
            ciphertext = EncryptionKey.encrypt(value.encode())
            return base64.b64encode(ciphertext).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    @classmethod
    def _decrypt(cls, encrypted: str, key_version: int) -> str:
        """
        Decrypt value using the configured backend.

        Handles both new format (backend-aware) and legacy format.
        """
        try:
            ciphertext = base64.b64decode(encrypted.encode())
            backend = EncryptionKey.get_backend()

            if not isinstance(backend, LocalKeyBackend):
                return backend.decrypt(ciphertext).decode()

            try:
                return backend.decrypt(ciphertext).decode()
            except Exception:
                if len(ciphertext) <= 28:
                    raise
                # Legacy format: nonce (12) + auth_tag (16) + data.
                return cls._decrypt_legacy(ciphertext, key_version)

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    @classmethod
    def _decrypt_legacy(cls, combined: bytes, key_version: int) -> str:
        """
        Decrypt legacy XOR-encrypted values.

        Provides backward compatibility for credentials encrypted before upgrade.
        """
        # Legacy format: nonce (12) + auth_tag (16) + encrypted_bytes
        auth_tag = combined[12:28]
        encrypted_bytes = combined[28:]

        # Get key for specified version
        backend = EncryptionKey.get_backend()
        if isinstance(backend, LocalKeyBackend):
            key = backend.get_key(key_version)
        else:
            # For non-local backends, derive a legacy key
            key = hashlib.sha256(b"flyto-dev-key-not-for-production").digest()

        # XOR decrypt
        decrypted_bytes = bytes(
            v ^ key[i % len(key)]
            for i, v in enumerate(encrypted_bytes)
        )
        value = decrypted_bytes.decode()

        # Verify HMAC
        h = hmac.new(key, value.encode(), hashlib.sha256)
        expected_tag = h.digest()[:16]

        if not hmac.compare_digest(auth_tag, expected_tag):
            raise ValueError("Authentication failed")

        return value
