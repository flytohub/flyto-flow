"""Encryption Key Management Facade"""

import logging
import os
from typing import Optional

from gateway.providers.loading import load_provider_factory
from services.credentials.backends import (
    AWSKMSBackend,
    KeyManagementBackend,
    LocalKeyBackend,
    VaultKeyBackend,
)

logger = logging.getLogger(__name__)


class EncryptionKey:
    """
    Encryption key management facade.

    Supports multiple backends:
    - local: Local key with PBKDF2 derivation (default)
    - vault: HashiCorp Vault transit engine
    - kms: AWS KMS
    - custom: Allowlisted provider for other KMS or HSM implementations

    Configure via FLYTO_KEY_BACKEND environment variable.
    """

    _backend: Optional[KeyManagementBackend] = None

    @classmethod
    def initialize(cls, master_key: Optional[str] = None) -> None:
        """
        Initialize encryption key backend.

        Args:
            master_key: Master key (for local backend only)
        """
        if cls._backend is not None:
            return

        backend_type = os.environ.get("FLYTO_KEY_BACKEND", "local").strip().lower()
        if backend_type not in {"local", "vault", "kms", "custom"}:
            raise ValueError(f"Unsupported FLYTO_KEY_BACKEND: {backend_type}")

        try:
            if backend_type == "custom":
                spec = os.environ.get("FLYTO_KEY_BACKEND_FACTORY", "").strip()
                if not spec:
                    raise ValueError(
                        "FLYTO_KEY_BACKEND=custom requires FLYTO_KEY_BACKEND_FACTORY"
                    )
                backend = load_provider_factory(
                    spec,
                    setting_name="FLYTO_KEY_BACKEND_FACTORY",
                )()
                if not isinstance(backend, KeyManagementBackend):
                    raise TypeError(
                        "Custom key backend must implement KeyManagementBackend"
                    )
                logger.info("Using custom key management backend")
            elif backend_type == "vault":
                backend = VaultKeyBackend()
                logger.info("Using HashiCorp Vault key backend")
            elif backend_type == "kms":
                backend = AWSKMSBackend()
                logger.info("Using AWS KMS key backend")
            else:
                backend = LocalKeyBackend(master_key)
                logger.info("Using local key backend")
            backend.validate_configuration()
            cls._backend = backend
        except Exception as e:
            cls._backend = None
            raise RuntimeError(
                f"Failed to initialize configured {backend_type} key backend"
            ) from e

    @classmethod
    def reset(cls) -> None:
        """Clear the process-local backend, primarily for controlled reconfiguration."""
        cls._backend = None

    @classmethod
    def get_backend(cls) -> KeyManagementBackend:
        """Get the key management backend."""
        if cls._backend is None:
            cls.initialize()
        return cls._backend

    @classmethod
    def get_key(cls, version: int) -> bytes:
        """Get encryption key by version."""
        backend = cls.get_backend()
        if isinstance(backend, LocalKeyBackend):
            return backend.get_key(version)
        # For Vault/KMS, generate a local derived key
        return backend.get_key(version)

    @classmethod
    def get_current_version(cls) -> int:
        """Get current key version."""
        return cls.get_backend().get_current_version()

    @classmethod
    def rotate_key(cls, new_master_key: Optional[str] = None) -> int:
        """
        Rotate to a new encryption key.

        Args:
            new_master_key: New master key (ignored for Vault/KMS)

        Returns:
            New key version
        """
        return cls.get_backend().rotate_key()

    @classmethod
    def encrypt(cls, plaintext: bytes) -> bytes:
        """Encrypt data using current backend."""
        return cls.get_backend().encrypt(plaintext)

    @classmethod
    def decrypt(cls, ciphertext: bytes) -> bytes:
        """Decrypt data using current backend."""
        return cls.get_backend().decrypt(ciphertext)
