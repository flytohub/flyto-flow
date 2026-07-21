"""User deletion provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence


class UserDeletionProvider(ABC):
    """Provider interface for GDPR user-data deletion side effects."""

    @abstractmethod
    async def mark_purchases_source_deleted_for_creator(self, user_id: str) -> int:
        """Mark purchases of templates owned by this user as source_deleted."""
        pass

    @abstractmethod
    async def delete_documents_by_field(
        self,
        collection: str,
        field: str,
        value: str,
        batch_size: int,
        dry_run: bool = False,
    ) -> int:
        """Delete or count documents matching a collection field."""
        pass

    @abstractmethod
    async def delete_user_subcollection_documents(
        self,
        user_id: str,
        subcollection: str,
        batch_size: int,
        dry_run: bool = False,
    ) -> int:
        """Delete or count documents in users/{user_id}/{subcollection}."""
        pass

    @abstractmethod
    async def delete_user_document(self, user_id: str, dry_run: bool = False) -> bool:
        """Delete or count the main users/{user_id} document."""
        pass

    @abstractmethod
    async def delete_storage_files(
        self,
        user_id: str,
        prefixes: Sequence[str],
        dry_run: bool = False,
    ) -> int:
        """Delete or count user-owned storage files for the given prefixes."""
        pass

    @abstractmethod
    async def delete_auth_user(self, user_id: str) -> bool:
        """Delete the user's auth identity."""
        pass
