"""
Simple Access Provider

Basic role-based access control for Cloud mode.
Supports admin/user roles with simple permission mapping.
"""

import logging
from typing import List

from gateway.providers.base import AccessControlProvider, UserInfo

logger = logging.getLogger(__name__)


# Simple permission to role mapping
ADMIN_PERMISSIONS = {
    "admin.read",
    "admin.write",
    "users.read",
    "users.write",
    "templates.publish",
    "templates.delete",
    "payments.read",
    "payments.manage",
    "settings.read",
    "settings.write",
}

USER_PERMISSIONS = {
    "templates.create",
    "templates.read",
    "templates.edit",
    "workflows.run",
    "workflows.view",
    "profile.read",
    "profile.edit",
}


class SimpleAccessProvider(AccessControlProvider):
    """
    Simple access control for Cloud mode.

    Uses basic admin/user role distinction.
    Admins have full access, users have limited permissions.
    """

    def __init__(self):
        """Initialize simple access provider."""
        pass

    @property
    def name(self) -> str:
        return "simple"

    async def check_permission(
        self,
        user: UserInfo,
        permission: str,
        resource: str = None
    ) -> bool:
        """
        Check if user has permission.

        Args:
            user: User info
            permission: Permission to check
            resource: Optional resource ID (ignored in simple mode)

        Returns:
            True if user has permission
        """
        if not user:
            return False

        # Admins have all permissions
        if user.is_admin or "admin" in user.roles:
            return True

        # Check if permission is in user's allowed set
        if permission in USER_PERMISSIONS:
            return True

        # Check admin permissions only for admins
        if permission in ADMIN_PERMISSIONS:
            return False

        # Default allow for unspecified permissions
        return True

    async def get_user_permissions(self, user: UserInfo) -> List[str]:
        """
        Get all permissions for user.

        Args:
            user: User info

        Returns:
            List of permission strings
        """
        if not user:
            return []

        if user.is_admin or "admin" in user.roles:
            return list(ADMIN_PERMISSIONS | USER_PERMISSIONS)

        return list(USER_PERMISSIONS)

    async def get_accessible_pages(self, user: UserInfo) -> List[str]:
        """
        Get pages accessible to user.

        Args:
            user: User info

        Returns:
            List of accessible page paths
        """
        if not user:
            return ["/login", "/register", "/marketplace"]

        base_pages = [
            "/",
            "/dashboard",
            "/my-templates",
            "/templates/builder",
            "/marketplace",
            "/settings",
            "/tools",
            "/plugins",
        ]

        if user.is_admin or "admin" in user.roles:
            base_pages.extend([
                "/admin",
                "/admin/dashboard",
                "/admin/users",
                "/admin/templates",
                "/admin/payments",
                "/admin/settings",
            ])

        return base_pages

    async def has_role(self, user: UserInfo, role: str) -> bool:
        """
        Check if user has role.

        Args:
            user: User info
            role: Role to check

        Returns:
            True if user has role
        """
        if not user:
            return False

        if role == "admin":
            return user.is_admin or "admin" in user.roles

        return role in user.roles

    async def assign_role(
        self,
        user_id: str,
        role: str,
        assigned_by: str,
        scope: str = None
    ) -> bool:
        """
        Assign role to user.

        In simple mode, role assignment is not persisted.
        Roles are determined by Firebase custom claims or database.

        Args:
            user_id: User to assign role to
            role: Role to assign
            assigned_by: Who is assigning the role
            scope: Optional scope (ignored)

        Returns:
            False - role assignment not supported in simple mode
        """
        logger.warning(
            "Role assignment not supported in simple mode. "
            "Use Firebase Admin SDK to set custom claims."
        )
        return False

    async def revoke_role(self, user_id: str, role: str) -> bool:
        """
        Revoke role from user.

        In simple mode, role revocation is not persisted.

        Args:
            user_id: User to revoke role from
            role: Role to revoke

        Returns:
            False - role revocation not supported in simple mode
        """
        logger.warning(
            "Role revocation not supported in simple mode. "
            "Use Firebase Admin SDK to modify custom claims."
        )
        return False
