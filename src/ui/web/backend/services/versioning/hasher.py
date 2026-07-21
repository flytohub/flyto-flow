"""
Content Hasher

Single responsibility: Generate deterministic content hashes.
"""

import hashlib
import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ContentHasher:
    """
    Generate deterministic hashes for workflow content.

    Uses SHA-256 for hashing normalized JSON content.
    """

    @staticmethod
    def hash_workflow(definition: Dict[str, Any]) -> str:
        """
        Hash a workflow definition.

        Normalizes the JSON before hashing to ensure
        identical content produces identical hashes.

        Args:
            definition: Workflow definition dictionary

        Returns:
            SHA-256 hash string
        """
        normalized = ContentHasher.normalize_json(definition)
        return ContentHasher.compute_sha256(normalized)

    @staticmethod
    def normalize_json(data: Any) -> str:
        """
        Normalize JSON data for consistent hashing.

        Ensures:
        - Keys are sorted
        - No extra whitespace
        - Consistent encoding

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

    @staticmethod
    def compute_sha256(content: str) -> str:
        """
        Compute SHA-256 hash of content.

        Args:
            content: String content to hash

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_dict(data: Dict[str, Any]) -> str:
        """
        Hash a dictionary.

        Convenience method for hashing arbitrary dictionaries.

        Args:
            data: Dictionary to hash

        Returns:
            SHA-256 hash string
        """
        normalized = ContentHasher.normalize_json(data)
        return ContentHasher.compute_sha256(normalized)

    @staticmethod
    def verify_hash(definition: Dict[str, Any], expected_hash: str) -> bool:
        """
        Verify that a definition matches expected hash.

        Args:
            definition: Workflow definition
            expected_hash: Expected SHA-256 hash

        Returns:
            True if hashes match
        """
        actual_hash = ContentHasher.hash_workflow(definition)
        return actual_hash == expected_hash
