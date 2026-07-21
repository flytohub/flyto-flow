"""
License Provider Interface
"""

from abc import ABC, abstractmethod


class LicenseProvider(ABC):
    """
    License data provider interface.

    Deployment-specific implementations may use hosted, enterprise, or local
    persistence without exposing that storage choice to callers.
    """

    @abstractmethod
    async def list_licenses(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str = None,
    ) -> dict:
        """List all licenses."""
        pass

    @abstractmethod
    async def get_license_stats(self) -> dict:
        """Get license statistics."""
        pass

    @abstractmethod
    async def get_license(self, license_id: str) -> dict:
        """Get single license."""
        pass

    @abstractmethod
    async def extend_license(self, license_id: str) -> dict:
        """Extend license by 1 year."""
        pass

    @abstractmethod
    async def revoke_license(self, license_id: str) -> dict:
        """Revoke license."""
        pass

    @abstractmethod
    async def add_device(self, license_id: str, device: dict) -> dict:
        """Add device to license."""
        pass

    @abstractmethod
    async def list_user_licenses(self, user_id: str) -> dict:
        """List licenses for a specific user."""
        pass

    @abstractmethod
    async def remove_device(self, license_id: str, fingerprint: str) -> dict:
        """Remove device from license."""
        pass

    @abstractmethod
    async def generate_license_file(self, license_id: str) -> dict:
        """Generate downloadable license file content."""
        pass

    @abstractmethod
    async def transfer_license(
        self,
        license_id: str,
        from_user_id: str,
        target_email: str,
    ) -> dict:
        """Transfer license to another user."""
        pass
