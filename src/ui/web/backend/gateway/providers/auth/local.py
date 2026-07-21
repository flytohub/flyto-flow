"""
Local Auth Provider

Authentication for desktop (local) mode.
Proxies token verification to the Cloud API so desktop users
get the same auth experience without a hosted identity SDK locally.
"""

import logging
from typing import Dict, Any

import httpx

from gateway.providers.base import AuthProvider, AuthResult, UserInfo

logger = logging.getLogger(__name__)


class LocalAuthProvider(AuthProvider):
    """
    Local authentication provider for desktop mode.

    Verifies hosted identity tokens by proxying to the Cloud API.
    This avoids bundling a hosted identity SDK in the desktop binary.
    """

    def __init__(self, cloud_api_url: str = ""):
        from config.settings import get_settings
        self.cloud_api_url = cloud_api_url or get_settings().cloud_api_url
        self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.cloud_api_url,
                timeout=httpx.Timeout(15.0, connect=5.0),
                follow_redirects=False,
            )
        return self._client

    @property
    def provider_name(self) -> str:
        """Return the provider name identifier."""
        return "local"

    async def verify_token(self, token: str) -> AuthResult:
        """
        Verify token by proxying to Cloud API's auth/me endpoint.

        The Cloud API verifies the identity token and returns user info.
        """
        try:
            client = await self._get_client()
            resp = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

            if resp.status_code != 200:
                return AuthResult(ok=False, error="Token verification failed")

            data = resp.json()
            if not data.get("ok") and not data.get("id"):
                return AuthResult(ok=False, error=data.get("error", "Invalid token"))

            # Cloud API returns user data directly
            user_data = data.get("user", data)

            user = UserInfo(
                id=user_data.get("id", user_data.get("uid", "")),
                email=user_data.get("email", ""),
                username=user_data.get("username", ""),
                display_name=user_data.get("displayName", user_data.get("display_name", "")),
                avatar_url=user_data.get("avatarUrl", user_data.get("avatar_url")),
                roles=user_data.get("roles", ["user"]),
                is_admin=user_data.get("isAdmin", user_data.get("is_admin", False)),
                subscription_plan=user_data.get("subscriptionPlan", user_data.get("subscription_plan")),
                subscription_status=user_data.get("subscriptionStatus", user_data.get("subscription_status")),
                allowed_languages=user_data.get("allowedLanguages", user_data.get("allowed_languages")),
                metadata={"provider": "local_proxy"},
            )

            return AuthResult(ok=True, user=user)

        except httpx.ConnectError:
            logger.warning("Cloud API unreachable for token verification")
            return AuthResult(ok=False, error="Cloud API unavailable")
        except httpx.TimeoutException:
            logger.warning("Cloud API timeout during token verification")
            return AuthResult(ok=False, error="Cloud API timeout")
        except Exception as e:
            logger.error(f"Local auth verification failed: {e}")
            return AuthResult(ok=False, error=f"Verification failed: {str(e)}")

    async def authenticate(self, credentials: Dict[str, Any]) -> AuthResult:
        """Proxy authentication to Cloud API."""
        try:
            client = await self._get_client()
            resp = await client.post("/api/auth/login", json=credentials)
            data = resp.json()

            if not data.get("ok"):
                return AuthResult(ok=False, error=data.get("error", "Authentication failed"))

            return AuthResult(
                ok=True,
                token=data.get("accessToken"),
                refresh_token=data.get("refreshToken"),
            )
        except Exception as e:
            logger.error(f"Local auth failed: {e}")
            return AuthResult(ok=False, error=f"Authentication failed: {str(e)}")

    async def refresh(self, refresh_token: str) -> AuthResult:
        """Proxy token refresh to Cloud API."""
        try:
            client = await self._get_client()
            resp = await client.post("/api/auth/refresh", json={"refreshToken": refresh_token})
            data = resp.json()

            if not data.get("ok"):
                return AuthResult(ok=False, error=data.get("error", "Refresh failed"))

            return AuthResult(
                ok=True,
                token=data.get("accessToken"),
                refresh_token=data.get("refreshToken"),
            )
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return AuthResult(ok=False, error=f"Refresh failed: {str(e)}")
