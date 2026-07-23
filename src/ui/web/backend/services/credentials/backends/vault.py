"""HashiCorp Vault Key Management Backend"""

import base64
import logging
import os
from typing import Optional
from urllib.parse import urlparse

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
        token_file = os.environ.get("VAULT_TOKEN_FILE", "").strip()
        if not self._vault_token and token_file:
            token_path = os.path.abspath(os.path.expanduser(token_file))
            if not os.path.isfile(token_path):
                raise ValueError("VAULT_TOKEN_FILE does not exist")
            if os.path.getsize(token_path) > 64 * 1024:
                raise ValueError("VAULT_TOKEN_FILE is too large")
            with open(token_path, encoding="utf-8") as stream:
                self._vault_token = stream.read(64 * 1024).strip()
        self._key_name = os.environ.get("VAULT_TRANSIT_KEY", key_name)
        self._mount_point = os.environ.get("VAULT_TRANSIT_MOUNT_POINT", "transit")
        self._namespace = os.environ.get("VAULT_NAMESPACE", "").strip() or None
        self._current_version = 1

        if not self._vault_addr or not self._vault_token:
            raise ValueError("VAULT_ADDR and VAULT_TOKEN required for Vault backend")
        parsed = urlparse(self._vault_addr)
        allow_insecure = os.environ.get("VAULT_ALLOW_INSECURE", "false").lower() == "true"
        if parsed.scheme != "https" and not (
            allow_insecure and parsed.hostname in {"127.0.0.1", "localhost"}
        ):
            raise ValueError("Vault requires HTTPS outside an explicit local development mode")

        # Import hvac if available
        try:
            import hvac
            verify: bool | str = True
            ca_cert = os.environ.get("VAULT_CACERT", "").strip()
            if ca_cert:
                ca_path = os.path.abspath(os.path.expanduser(ca_cert))
                if not os.path.isfile(ca_path):
                    raise ValueError("VAULT_CACERT does not exist")
                verify = ca_path
            self._client = hvac.Client(
                url=self._vault_addr,
                token=self._vault_token,
                namespace=self._namespace,
                verify=verify,
            )
        except ImportError:
            raise ImportError("hvac library required for Vault backend")

    def validate_configuration(self) -> None:
        """Verify Transit encrypt and decrypt permissions before readiness."""
        probe = b"flyto2-vault-readiness"
        try:
            if self.decrypt(self.encrypt(probe)) != probe:
                raise RuntimeError("Vault Transit readiness round trip failed")
        except Exception as exc:
            raise RuntimeError("Vault Transit validation failed") from exc

    def get_key(self, version: int) -> bytes:
        """Not applicable for Vault - keys never leave Vault."""
        raise NotImplementedError("Vault keys are never exported")

    def get_current_version(self) -> int:
        """Get current key version from Vault."""
        try:
            response = self._client.secrets.transit.read_key(
                name=self._key_name,
                mount_point=self._mount_point,
            )
            version = response["data"]["latest_version"]
            if not isinstance(version, int) or version < 1:
                raise ValueError("Vault returned an invalid latest key version")
            self._current_version = version
            return version
        except Exception as exc:
            logger.error("Failed to get Vault key version")
            raise RuntimeError("Failed to get current Vault key version") from exc

    def rotate_key(self) -> int:
        """Rotate key in Vault."""
        try:
            self._client.secrets.transit.rotate_key(
                name=self._key_name,
                mount_point=self._mount_point,
            )
            self._current_version = self.get_current_version()
            logger.info(f"Rotated Vault key to version {self._current_version}")
            return self._current_version
        except Exception:
            logger.error("Failed to rotate Vault key")
            raise

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt using Vault transit engine."""
        try:
            # Base64 encode for Vault API
            b64_plaintext = base64.b64encode(plaintext).decode()

            response = self._client.secrets.transit.encrypt_data(
                name=self._key_name,
                plaintext=b64_plaintext,
                mount_point=self._mount_point,
            )
            ciphertext = response["data"]["ciphertext"]
            parts = ciphertext.split(":", 2)
            if len(parts) >= 2 and parts[1].startswith("v"):
                self._current_version = int(parts[1][1:])
            return b"FVAULT1:" + ciphertext.encode()
        except Exception:
            logger.error("Vault encryption failed")
            raise

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt using Vault transit engine."""
        try:
            if not ciphertext.startswith(b"FVAULT1:"):
                raise ValueError("Invalid Vault ciphertext envelope")
            response = self._client.secrets.transit.decrypt_data(
                name=self._key_name,
                ciphertext=ciphertext.removeprefix(b"FVAULT1:").decode(),
                mount_point=self._mount_point,
            )
            b64_plaintext = response["data"]["plaintext"]
            return base64.b64decode(b64_plaintext, validate=True)
        except Exception:
            logger.error("Vault decryption failed")
            raise
