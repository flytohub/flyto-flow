"""Local Key Management Backend"""

import hashlib
import hmac
import json
import logging
import os
import secrets
from typing import Dict, Optional

from services.credentials.backends.base import KeyManagementBackend

logger = logging.getLogger(__name__)

# Check for cryptography library
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    # SECURITY: Check if in production - cryptography is required
    is_debug = os.environ.get("DEBUG", "false").lower() == "true"
    if not is_debug:
        raise ImportError(
            "CRITICAL: cryptography library is required in production. "
            "Install with: pip install cryptography>=44.0.1"
        )
    logger.warning("cryptography library not found, using fallback encryption (DEV MODE ONLY)")


class LocalKeyBackend(KeyManagementBackend):
    """
    Local key management with PBKDF2 key derivation.

    Uses AES-256-GCM for encryption.
    """

    def __init__(self, master_key: Optional[str] = None):
        """Initialize with master key."""
        self._keys: Dict[int, bytes] = {}

        # Check if running in production (DEBUG not set or false)
        is_debug = os.environ.get("DEBUG", "false").lower() == "true"

        raw_version = os.environ.get("FLYTO_ENCRYPTION_KEY_VERSION", "1")
        try:
            self._current_version = int(raw_version)
        except ValueError as exc:
            raise RuntimeError("FLYTO_ENCRYPTION_KEY_VERSION must be an integer") from exc
        if not 1 <= self._current_version <= 255:
            raise RuntimeError("FLYTO_ENCRYPTION_KEY_VERSION must be between 1 and 255")

        # SECURITY: Salt must be unique per deployment
        env_salt = os.environ.get("FLYTO_KEY_SALT")
        if env_salt:
            if not is_debug and len(env_salt) < 16:
                raise RuntimeError("FLYTO_KEY_SALT must contain at least 16 characters")
            self._salt = env_salt.encode()
        else:
            if not is_debug:
                raise RuntimeError(
                    "CRITICAL: FLYTO_KEY_SALT environment variable is required in production. "
                    "Generate a unique salt with: python -c \"import secrets; print(secrets.token_hex(16))\""
                )
            # Dev mode: use a deterministic but clearly marked dev salt
            logger.warning(
                "SECURITY WARNING: Using development salt. "
                "Set FLYTO_KEY_SALT for production use."
            )
            self._salt = b"flyto-dev-salt-not-for-production"

        # Get master key
        if master_key:
            active_master_key = master_key
        else:
            env_key = os.environ.get("FLYTO_ENCRYPTION_KEY")
            if env_key:
                active_master_key = env_key
            else:
                # SECURITY: In production, require explicit encryption key
                if not is_debug:
                    raise RuntimeError(
                        "CRITICAL: FLYTO_ENCRYPTION_KEY environment variable is required in production. "
                        "Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\""
                    )
                # Only allow dev key in debug mode
                logger.warning(
                    "SECURITY WARNING: Using development encryption key. "
                    "Set FLYTO_ENCRYPTION_KEY for production use."
                )
                active_master_key = "flyto-dev-key-not-for-production"

        if not is_debug and len(active_master_key) < 32:
            raise RuntimeError("FLYTO_ENCRYPTION_KEY must contain at least 32 characters")

        self._master_keys: Dict[int, bytes] = {
            self._current_version: active_master_key.encode()
        }
        raw_previous_keys = os.environ.get("FLYTO_ENCRYPTION_PREVIOUS_KEYS", "").strip()
        if raw_previous_keys:
            try:
                previous_keys = json.loads(raw_previous_keys)
            except json.JSONDecodeError as exc:
                raise RuntimeError("FLYTO_ENCRYPTION_PREVIOUS_KEYS must be valid JSON") from exc
            if not isinstance(previous_keys, dict):
                raise RuntimeError("FLYTO_ENCRYPTION_PREVIOUS_KEYS must be a JSON object")
            for raw_key_version, previous_master_key in previous_keys.items():
                try:
                    key_version = int(raw_key_version)
                except (TypeError, ValueError) as exc:
                    raise RuntimeError("Previous encryption key versions must be integers") from exc
                if not 1 <= key_version <= 255 or key_version == self._current_version:
                    raise RuntimeError("Previous encryption key versions must be unique values between 1 and 255")
                if not isinstance(previous_master_key, str) or not previous_master_key:
                    raise RuntimeError("Previous encryption master keys must be non-empty strings")
                if not is_debug and len(previous_master_key) < 32:
                    raise RuntimeError("Previous encryption master keys must contain at least 32 characters")
                self._master_keys[key_version] = previous_master_key.encode()

        # Derive initial key
        self._keys[self._current_version] = self._derive_key(
            self._master_keys[self._current_version],
            self._current_version,
        )

    def _derive_key(self, master_key: bytes, version: int) -> bytes:
        """Derive encryption key using PBKDF2."""
        if HAS_CRYPTOGRAPHY:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256 bits for AES-256
                salt=self._salt + str(version).encode(),
                iterations=100000,
                backend=default_backend(),
            )
            return kdf.derive(master_key)
        else:
            # Fallback to hashlib
            return hashlib.pbkdf2_hmac(
                "sha256",
                master_key,
                self._salt + str(version).encode(),
                100000,
                32,
            )

    def get_key(self, version: int) -> bytes:
        """Get encryption key by version."""
        if version not in self._keys:
            master_key = self._master_keys.get(version)
            if master_key is None:
                # Compatibility for credentials written by the old in-process
                # rotation implementation, which reused one master key.
                if self._current_version == 1 and len(self._master_keys) == 1:
                    master_key = self._master_keys[self._current_version]
                else:
                    raise ValueError(f"Encryption key version {version} is not configured")
            self._keys[version] = self._derive_key(master_key, version)
        return self._keys[version]

    def get_current_version(self) -> int:
        """Get current key version."""
        return self._current_version

    def rotate_key(self) -> int:
        """Reject process-local rotation that cannot coordinate replicas."""
        raise RuntimeError(
            "Local encryption keys must be rotated through deployment configuration "
            "using FLYTO_ENCRYPTION_KEY_VERSION and FLYTO_ENCRYPTION_PREVIOUS_KEYS"
        )

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt using AES-256-GCM."""
        key = self.get_key(self._current_version)
        nonce = secrets.token_bytes(12)

        if HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        else:
            # Fallback XOR encryption (not recommended for production)
            logger.warning("Using fallback XOR encryption - install cryptography!")
            ciphertext = bytes(
                p ^ key[i % len(key)] for i, p in enumerate(plaintext)
            )
            # Add simple MAC
            mac = hmac.new(key, plaintext, hashlib.sha256).digest()[:16]
            ciphertext = mac + ciphertext

        # Format: version (1 byte) + nonce (12 bytes) + ciphertext
        return bytes([self._current_version]) + nonce + ciphertext

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt using AES-256-GCM."""
        if len(ciphertext) < 14:
            raise ValueError("Ciphertext too short")

        version = ciphertext[0]
        nonce = ciphertext[1:13]
        encrypted = ciphertext[13:]

        key = self.get_key(version)

        if HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(nonce, encrypted, None)
        else:
            # Fallback XOR decryption
            mac = encrypted[:16]
            data = encrypted[16:]
            plaintext = bytes(
                d ^ key[i % len(key)] for i, d in enumerate(data)
            )
            # Verify MAC
            expected_mac = hmac.new(key, plaintext, hashlib.sha256).digest()[:16]
            if not hmac.compare_digest(mac, expected_mac):
                raise ValueError("Authentication failed")
            return plaintext
