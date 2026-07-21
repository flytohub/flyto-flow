"""
Provider Base Classes

Abstract base classes defining the interface for all providers.
Each provider type has Cloud and Enterprise implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class UserInfo(BaseModel):
    """
    Unified user information structure.

    Used across all providers to ensure consistent user representation.
    """
    id: str = Field(..., description="Unique user identifier")
    email: Optional[str] = Field(None, description="User email address")
    username: Optional[str] = Field(None, description="Username/login name")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    roles: List[str] = Field(default_factory=list, description="Assigned roles")
    groups: List[str] = Field(default_factory=list, description="Group memberships")
    organization_id: Optional[str] = Field(None, description="Organization ID (Enterprise)")
    is_admin: bool = Field(False, description="Admin flag")
    is_active: bool = Field(True, description="Account active status")
    subscription_plan: Optional[str] = Field(None, description="Subscription plan (free/pro/team/enterprise)")
    subscription_status: Optional[str] = Field(None, description="Subscription status (active/cancelled/expired)")
    allowed_languages: Optional[List[str]] = Field(None, description="Languages this user can access (None = all)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(frozen=False)


class AuthResult(BaseModel):
    """Authentication result from any auth provider"""
    ok: bool = Field(..., description="Authentication success")
    user: Optional[UserInfo] = Field(None, description="User info if authenticated")
    error: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code for i18n")
    token: Optional[str] = Field(None, description="Access token if applicable")
    refresh_token: Optional[str] = Field(None, description="Refresh token if applicable")


class AuthProvider(ABC):
    """
    Authentication provider abstraction.

    Implementations support managed cloud identity and enterprise
    LDAP/SAML/OIDC/JWT authentication behind this contract.
    """

    @abstractmethod
    async def verify_token(self, token: str) -> AuthResult:
        """
        Verify authentication token.

        Args:
            token: Bearer token from Authorization header

        Returns:
            AuthResult with user info if valid
        """
        pass

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthResult:
        """
        Authenticate with credentials.

        Args:
            credentials: Provider-specific credential dictionary, such as an
                identity token or username/password pair.

        Returns:
            AuthResult with user info and tokens if successful
        """
        pass

    @abstractmethod
    async def refresh(self, refresh_token: str) -> AuthResult:
        """
        Refresh authentication token.

        Args:
            refresh_token: Refresh token

        Returns:
            AuthResult with new tokens
        """
        pass

    async def change_password(
        self,
        *,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> Dict[str, Any]:
        """Change a local password when the identity provider supports it."""
        raise NotImplementedError(
            f"{self.provider_name} does not support backend password changes"
        )

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g., 'firebase', 'ldap')"""
        pass

    def get_frontend_config(self) -> Dict[str, Any]:
        """Return public auth configuration consumed by the frontend."""
        return {
            "google": {
                "enabled": False,
                "clientId": None,
                "desktopClientId": None,
            },
            "github": {
                "enabled": False,
                "clientId": None,
            },
            "allowSelfSignup": True,
        }

    async def exchange_desktop_oauth_code(
        self,
        provider: str,
        *,
        code: str,
        redirect_uri: str,
    ) -> Dict[str, Any]:
        """Exchange a desktop OAuth callback code for provider auth tokens."""
        raise NotImplementedError(
            f"{self.provider_name} does not support desktop OAuth code exchange"
        )

    async def sign_in_with_google_credential(
        self,
        credential: str,
        *,
        request_uri: str,
    ) -> Dict[str, Any]:
        """Sign in or register with a Google credential."""
        raise NotImplementedError(
            f"{self.provider_name} does not support Google credential sign-in"
        )

    async def sign_in_with_google_code(
        self,
        *,
        code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None,
        use_desktop_client: bool = False,
    ) -> Dict[str, Any]:
        """Exchange a Google OAuth code and sign in with the auth provider."""
        raise NotImplementedError(
            f"{self.provider_name} does not support Google OAuth code sign-in"
        )

    async def sign_in_with_github_code(
        self,
        *,
        code: str,
        redirect_uri: str,
        request_uri: str,
    ) -> Dict[str, Any]:
        """Exchange a GitHub OAuth code and sign in with the auth provider."""
        raise NotImplementedError(
            f"{self.provider_name} does not support GitHub OAuth code sign-in"
        )

    async def get_account_providers(self, id_token: str) -> Optional[List[str]]:
        """Return linked login provider IDs for an account."""
        raise NotImplementedError(
            f"{self.provider_name} does not support linked-provider lookup"
        )

    async def link_google_account(
        self,
        *,
        id_token: str,
        credential: str,
        request_uri: str,
    ) -> Optional[List[str]]:
        """Link a Google account to an existing authenticated account."""
        raise NotImplementedError(
            f"{self.provider_name} does not support Google account linking"
        )

    async def unlink_account_provider(
        self,
        *,
        id_token: str,
        provider_id: str,
    ) -> Optional[List[str]]:
        """Unlink one login provider from an existing authenticated account."""
        raise NotImplementedError(
            f"{self.provider_name} does not support account provider unlinking"
        )

    async def backfill_user_avatar(self, *, user_id: str, avatar_url: str) -> None:
        """Persist a provider profile avatar for a user when supported."""
        return None


class IdentityProvider(ABC):
    """
    Identity/User data provider abstraction.

    Implementations:
    - FirestoreIdentityProvider: Firestore users collection (Cloud)
    - PostgresIdentityProvider: PostgreSQL users table (Enterprise)
    """

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[UserInfo]:
        """Get user by ID"""
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserInfo]:
        """Get user by email"""
        pass

    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any]) -> UserInfo:
        """Create new user"""
        pass

    @abstractmethod
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> UserInfo:
        """Update user data"""
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft or hard delete based on implementation)"""
        pass

    @abstractmethod
    async def list_users(
        self,
        organization_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> List[UserInfo]:
        """List users with pagination"""
        pass


class AccessControlProvider(ABC):
    """
    Access control provider abstraction.

    Implementations:
    - SimpleAccessProvider: Basic role check - user/admin (Cloud)
    - RBACAccessProvider: Full RBAC with fine-grained permissions (Enterprise)
    """

    @abstractmethod
    async def check_permission(
        self,
        user: UserInfo,
        permission: str,
        resource: Optional[str] = None
    ) -> bool:
        """
        Check if user has specific permission.

        Args:
            user: User to check
            permission: Permission string (e.g., "workflow.execute")
            resource: Optional resource ID for resource-level permissions

        Returns:
            True if user has permission
        """
        pass

    @abstractmethod
    async def get_user_permissions(self, user: UserInfo) -> List[str]:
        """Get all permissions for user"""
        pass

    @abstractmethod
    async def get_accessible_pages(self, user: UserInfo) -> List[str]:
        """
        Get list of page paths user can access.

        Returns:
            List of accessible page paths
        """
        pass

    @abstractmethod
    async def assign_role(
        self,
        user_id: str,
        role: str,
        assigned_by: str,
        scope: Optional[str] = None
    ) -> bool:
        """
        Assign role to user.

        Args:
            user_id: User to assign role to
            role: Role name
            assigned_by: ID of user making assignment
            scope: Optional scope (org, project, etc.)

        Returns:
            True if assignment successful
        """
        pass

    @abstractmethod
    async def revoke_role(self, user_id: str, role: str) -> bool:
        """Revoke role from user"""
        pass


class AuditProvider(ABC):
    """
    Audit logging provider abstraction.

    Implementations:
    - NoopAuditProvider: No audit logging (Cloud default)
    - FullAuditProvider: Complete audit trail (Enterprise)
    """

    @abstractmethod
    async def log(
        self,
        action: str,
        actor_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        result: str = "success",
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log audit event.

        Args:
            action: Action performed (e.g., "user.login", "workflow.execute")
            actor_id: ID of user performing action
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional details
            result: "success" or "failure"
            ip_address: Client IP address
        """
        pass

    @abstractmethod
    async def query(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query audit logs.

        Args:
            filters: Query filters (actor_id, action, date_range, etc.)
            limit: Max results
            offset: Pagination offset

        Returns:
            List of audit log entries
        """
        pass


class MarketplaceProvider(ABC):
    """
    Marketplace provider abstraction.

    Implementations:
    - CloudMarketplaceProvider: Full marketplace features (Cloud)
    - NoopMarketplaceProvider: Disabled marketplace (Enterprise)
    """

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if marketplace is enabled"""
        pass

    @abstractmethod
    async def list_templates(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List marketplace templates"""
        pass

    @abstractmethod
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get single template details"""
        pass

    @abstractmethod
    async def purchase(
        self,
        user_id: str,
        template_id: str,
        payment_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process template purchase"""
        pass

    @abstractmethod
    async def publish(
        self,
        user_id: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Publish template to marketplace"""
        pass
