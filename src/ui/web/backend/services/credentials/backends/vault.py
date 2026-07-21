"""HashiCorp Vault Key Management Backend"""

import base64
import logging
import os
from typing import Optional

from services.credentials.backends.base import KeyManagementBackend

logger = logging.getLogger(__name__)


class VaultKeyBackend(KeyManagementBackend):
    """
    HashiCorp Vault transit engine backend.

    Requires VAULT_ADDR and VAULT_TOKEN environment variables.
    """

    def __init__(
        self,
        vault_addr: Optional[str] = None,
        vault_token: Optional[str] = None,
        key_name: str = "flyto-credentials",
    ):
        """Initialize Vault backend."""
        self._vault_addr = vault_addr or os.environ.get("VAULT_ADDR")
        self._vault_token = vault_token or os.environ.get("VAULT_TOKEN")
        self._key_name = key_name
        self._current_version = 1

        if not self._vault_addr or not self._vault_token:
            raise ValueError("VAULT_ADDR and VAULT_TOKEN required for Vault backend")

        # Import hvac if available
        try:
            import hvac
            self._client = hvac.Client(
                url=self._vault_addr,
                token=self._vault_token,
            )
        except ImportError:
            raise ImportError("hvac library required for Vault backend")

    def get_key(self, version: int) -> bytes:
        """Not applicable for Vault - keys never leave Vault."""
        raise NotImplementedError("Vault keys are never exported")

    def get_current_version(self) -> int:
        """Get current key version from Vault."""
        try:
            response = self._client.secrets.transit.read_key(name=self._key_name)
            version = response["data"]["latest_version"]
            if not isinstance(version, int) or version < 1:
                raise ValueError("Vault returned an invalid latest key version")
            self._current_version = version
            return version
        except Exception as e:
            logger.error(f"Failed to get Vault key version: {e}")
            raise RuntimeError("Failed to get current Vault key version") from e

    def rotate_key(self) -> int:
        """Rotate key in Vault."""
        try:
            self._client.secrets.transit.rotate_key(name=self._key_name)
            self._current_version = self.get_current_version()
            logger.info(f"Rotated Vault key to version {self._current_version}")
            return self._current_version
        except Exception as e:
            logger.error(f"Failed to rotate Vault key: {e}")
            raise

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt using Vault transit engine."""
        try:
            # Base64 encode for Vault API
            b64_plaintext = base64.b64encode(plaintext).decode()

            response = self._client.secrets.transit.encrypt_data(
                name=self._key_name,
                plaintext=b64_plaintext,
            )
            ciphertext = response["data"]["ciphertext"]
            return ciphertext.encode()
        except Exception as e:
            logger.error(f"Vault encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt using Vault transit engine."""
        try:
            response = self._client.secrets.transit.decrypt_data(
                name=self._key_name,
                ciphertext=ciphertext.decode(),
            )
            b64_plaintext = response["data"]["plaintext"]
            return base64.b64decode(b64_plaintext)
        except Exception as e:
            logger.error(f"Vault decryption failed: {e}")
            raise
