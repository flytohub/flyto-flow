"""AWS KMS Key Management Backend"""

import logging
import os
import secrets
from typing import Optional

from services.credentials.backends.base import KeyManagementBackend

logger = logging.getLogger(__name__)
ENVELOPE_MAGIC = b"FKMS1"
ENCRYPTION_CONTEXT = {"application": "flyto2-flow", "purpose": "credentials"}

# Check for cryptography library
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class AWSKMSBackend(KeyManagementBackend):
    """
    AWS KMS backend for key management.

    Requires AWS credentials and KMS key ID.
    """

    def __init__(
        self,
        key_id: Optional[str] = None,
        region: Optional[str] = None,
    ):
        """Initialize AWS KMS backend."""
        self._key_id = key_id or os.environ.get("AWS_KMS_KEY_ID")
        self._region = region or os.environ.get("AWS_REGION", "us-east-1")
        self._current_version = 1

        if not self._key_id:
            raise ValueError("AWS_KMS_KEY_ID required for KMS backend")
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError(
                "cryptography with AES-GCM support is required for AWS KMS backend"
            )

        try:
            import boto3
            self._client = boto3.client("kms", region_name=self._region)
        except ImportError:
            raise ImportError("boto3 library required for AWS KMS backend")

    def validate_configuration(self) -> None:
        """Verify the configured key exists and can encrypt and decrypt."""
        try:
            response = self._client.describe_key(KeyId=self._key_id)
            metadata = response.get("KeyMetadata", {})
            if metadata.get("KeyState") != "Enabled":
                raise RuntimeError("AWS KMS key is not enabled")
            if metadata.get("KeyUsage") != "ENCRYPT_DECRYPT":
                raise RuntimeError("AWS KMS key does not support encryption")
            probe = b"flyto2-kms-readiness"
            if self.decrypt(self.encrypt(probe)) != probe:
                raise RuntimeError("AWS KMS readiness round trip failed")
        except Exception as exc:
            raise RuntimeError("AWS KMS key validation failed") from exc

    def get_key(self, version: int) -> bytes:
        """Generate data key from KMS."""
        try:
            response = self._client.generate_data_key(
                KeyId=self._key_id,
                KeySpec="AES_256",
                EncryptionContext=ENCRYPTION_CONTEXT,
            )
            return response["Plaintext"]
        except Exception:
            logger.error("Failed to generate KMS data key")
            raise

    def get_current_version(self) -> int:
        """KMS handles versioning internally."""
        return 1

    def rotate_key(self) -> int:
        """KMS handles rotation automatically if enabled."""
        logger.info("AWS KMS key rotation is managed by KMS")
        return 1

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt using AWS KMS (envelope encryption)."""
        try:
            # Generate data key
            response = self._client.generate_data_key(
                KeyId=self._key_id,
                KeySpec="AES_256",
                EncryptionContext=ENCRYPTION_CONTEXT,
            )
            data_key = response["Plaintext"]
            encrypted_key = response["CiphertextBlob"]

            # Encrypt data with data key
            aesgcm = AESGCM(data_key)
            nonce = secrets.token_bytes(12)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)

            # Format: key_len (2 bytes) + encrypted_key + nonce + ciphertext
            key_len = len(encrypted_key)
            if key_len > 65535:
                raise ValueError("KMS encrypted data key is too large")
            return ENVELOPE_MAGIC + key_len.to_bytes(2, "big") + encrypted_key + nonce + ciphertext
        except Exception:
            logger.error("KMS encryption failed")
            raise

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt using AWS KMS (envelope encryption)."""
        try:
            # Parse format
            modern = ciphertext.startswith(ENVELOPE_MAGIC)
            if modern:
                ciphertext = ciphertext[len(ENVELOPE_MAGIC):]
            elif (
                os.environ.get(
                    "FLYTO_KMS_ALLOW_LEGACY_CIPHERTEXT",
                    "false",
                ).strip().lower()
                != "true"
            ):
                raise ValueError(
                    "Legacy KMS ciphertext requires "
                    "FLYTO_KMS_ALLOW_LEGACY_CIPHERTEXT=true"
                )
            if len(ciphertext) < 2:
                raise ValueError("KMS ciphertext is too short")
            key_len = int.from_bytes(ciphertext[:2], "big")
            minimum_length = 2 + key_len + 12 + 16
            if key_len == 0 or len(ciphertext) < minimum_length:
                raise ValueError("Invalid KMS ciphertext envelope")
            encrypted_key = ciphertext[2 : 2 + key_len]
            nonce = ciphertext[2 + key_len : 2 + key_len + 12]
            encrypted_data = ciphertext[2 + key_len + 12 :]

            # Decrypt data key
            decrypt_args = {
                "CiphertextBlob": encrypted_key,
                "KeyId": self._key_id,
            }
            if modern:
                decrypt_args["EncryptionContext"] = ENCRYPTION_CONTEXT
            response = self._client.decrypt(**decrypt_args)
            data_key = response["Plaintext"]

            # Decrypt data
            aesgcm = AESGCM(data_key)
            return aesgcm.decrypt(nonce, encrypted_data, None)
        except Exception:
            logger.error("KMS decryption failed")
            raise
