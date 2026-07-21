"""
Audit Hasher

Single responsibility: Compute entry hashes for integrity.
"""

import hashlib
import json
import logging
from typing import Any, Dict

from services.audit.entry import AuditEntry

logger = logging.getLogger(__name__)


class AuditHasher:
    """
    Compute hashes for audit entries.

    Uses SHA-256 for integrity verification.
    """

    # Genesis hash for first entry in a chain
    GENESIS_HASH = "0" * 64

    @classmethod
    def compute_entry_hash(
        cls,
        entry: AuditEntry,
        prev_hash: str,
    ) -> str:
        """
        Compute hash for an audit entry.

        The hash is computed from:
        - Sequence number
        - Entry content
        - Previous entry hash

        Args:
            entry: Audit entry
            prev_hash: Hash of previous entry

        Returns:
            SHA-256 hash string
        """
        content = entry.get_hashable_content()
        combined = f"{content}|{prev_hash}"
        return cls.compute_sha256(combined)

    @classmethod
    def compute_value_hash(cls, value: Dict[str, Any]) -> str:
        """
        Compute hash of a value dictionary.

        Used for old_value_hash and new_value_hash fields.

        Args:
            value: Dictionary to hash

        Returns:
            SHA-256 hash string
        """
        normalized = cls.normalize_json(value)
        return cls.compute_sha256(normalized)

    @classmethod
    def compute_sha256(cls, content: str) -> str:
        """
        Compute SHA-256 hash of content.

        Args:
            content: String content to hash

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def normalize_json(cls, data: Any) -> str:
        """
        Normalize JSON data for consistent hashing.

        Args:
            data: Data to normalize

        Returns:
            Normalized JSON string
        """
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @classmethod
    def verify_entry_hash(cls, entry: AuditEntry) -> bool:
        """
        Verify an entry's hash is correct.

        Args:
            entry: Entry to verify

        Returns:
            True if hash is valid
        """
        expected = cls.compute_entry_hash(entry, entry.prev_entry_hash)
        return expected == entry.entry_hash

    @classmethod
    def verify_chain_link(
        cls,
        current: AuditEntry,
        previous: AuditEntry,
    ) -> bool:
        """
        Verify chain link between two consecutive entries.

        Args:
            current: Current entry
            previous: Previous entry

        Returns:
            True if chain is valid
        """
        # Verify sequence numbers are consecutive
        if current.sequence_number != previous.sequence_number + 1:
            return False

        # Verify prev_entry_hash points to previous entry
        if current.prev_entry_hash != previous.entry_hash:
            return False

        # Verify current entry's hash is valid
        return cls.verify_entry_hash(current)

    @classmethod
    def get_genesis_hash(cls) -> str:
        """Get the genesis hash for starting a new chain."""
        return cls.GENESIS_HASH
