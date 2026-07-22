"""
Shared dependencies for auth sub-modules.

Contains rate limiters, password validation, Pydantic models,
helper functions, and auth dependencies (get_current_user, get_optional_user).
"""

import logging
import re
import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Header
from pydantic import BaseModel, Field, EmailStr, field_validator

from gateway.providers.hub import get_auth_provider

logger = logging.getLogger(__name__)


# =============================================================================
# Password Validation Constants — imported from single source of truth
# =============================================================================

from common.validation_rules import PASSWORD_MIN_LENGTH  # noqa: E402


# =============================================================================
# Rate Limiting
# =============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter for authentication endpoints.

    SECURITY: Prevents brute force attacks on login/password reset.
    For production, consider Redis-based implementation for distributed systems.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 300,
        lockout_seconds: int = 900,
    ):
        """
        Initialize rate limiter.

        Args:
            max_attempts: Max attempts before lockout
            window_seconds: Time window for counting attempts (5 min default)
            lockout_seconds: Lockout duration after max attempts (15 min default)
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lockouts: dict[str, float] = {}

    def _clean_old_attempts(self, key: str) -> None:
        """Remove attempts outside the time window."""
        now = time.time()
        cutoff = now - self.window_seconds
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]

    def is_locked(self, key: str) -> bool:
        """Check if key is currently locked out."""
        if key not in self._lockouts:
            return False
        if time.time() > self._lockouts[key]:
            del self._lockouts[key]
            return False
        return True

    def get_lockout_remaining(self, key: str) -> int:
        """Get remaining lockout time in seconds."""
        if key not in self._lockouts:
            return 0
        remaining = int(self._lockouts[key] - time.time())
        return max(0, remaining)

    def record_attempt(self, key: str) -> bool:
        """
        Record an attempt and check if allowed.

        Returns:
            True if attempt is allowed, False if rate limited
        """
        if self.is_locked(key):
            return False

        self._clean_old_attempts(key)
        self._attempts[key].append(time.time())

        if len(self._attempts[key]) > self.max_attempts:
            self._lockouts[key] = time.time() + self.lockout_seconds
            logger.warning(f"Rate limit exceeded for key: {key[:20]}...")
            return False

        return True

    def reset(self, key: str) -> None:
        """Reset attempts for a key (call on successful login)."""
        self._attempts.pop(key, None)
        self._lockouts.pop(key, None)


# Global rate limiters
login_rate_limiter = RateLimiter(max_attempts=5, window_seconds=300, lockout_seconds=900)
password_reset_rate_limiter = RateLimiter(max_attempts=3, window_seconds=3600, lockout_seconds=3600)


def mask_email(email: str) -> str:
    """Mask email for logging (privacy protection)."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"**@{domain}"
    return f"{local[:2]}***@{domain}"


# =============================================================================
# Request/Response Models
# =============================================================================


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """Register request for providers that support self-registration."""
    email: EmailStr
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH)
    username: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password complexity requirements."""
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class AuthResponse(BaseModel):
    """Authentication response."""
    ok: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    user: Optional[dict] = None
    must_change_password: bool = False
    error: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=PASSWORD_MIN_LENGTH)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password complexity requirements."""
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserResponse(BaseModel):
    """User info response."""
    id: str
    email: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    is_admin: bool = False
    roles: list = []
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    allowed_languages: Optional[list] = None
    # S-Grade: Pre-computed Pro status
    is_pro: bool = False


class RefreshTokenRequest(BaseModel):
    """Request to refresh an access token using a refresh token."""
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Request to initiate password reset."""
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    """Request to verify reset code (Firebase oobCode)."""
    code: str = Field(..., min_length=1)


class ResetPasswordRequest(BaseModel):
    """Request to reset password with Firebase oobCode."""
    code: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=PASSWORD_MIN_LENGTH)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password complexity requirements."""
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class GoogleLoginRequest(BaseModel):
    """Google login request."""
    credential: str = Field(..., min_length=1)


class GoogleLoginCodeRequest(BaseModel):
    """Google login via authorization code (desktop OAuth flow)."""
    code: str = Field(..., min_length=1)
    redirect_uri: str = Field(..., min_length=1)
    code_verifier: Optional[str] = None


class GitHubLoginRequest(BaseModel):
    """GitHub login request."""
    code: str = Field(..., min_length=1)
    redirect_uri: Optional[str] = None  # Desktop OAuth provides this explicitly


class LinkGoogleRequest(BaseModel):
    """Link Google account request."""
    credential: str = Field(..., min_length=1)


class UnlinkProviderRequest(BaseModel):
    """Unlink provider request."""
    provider_id: str = Field(..., min_length=1)


class VscodeCodeRequest(BaseModel):
    """Request from landing page with Firebase ID token."""
    firebase_token: str = Field(..., min_length=1)


class ExchangeCodeRequest(BaseModel):
    """Request from VSCode extension to exchange auth code for tokens."""
    code: str = Field(..., min_length=1)


# =============================================================================
# Pro Status Helpers
# =============================================================================

# S-Grade: Constants for Pro access computation — canonical location: common.billing
from common.billing import PRO_PLANS, ACTIVE_STATUSES  # noqa: E402


def compute_is_pro(user_data: dict) -> bool:
    """
    Compute Pro status on backend.
    Pro is determined solely by subscription plan + status.
    """
    plan = user_data.get("subscription_plan")
    status = user_data.get("subscription_status")
    return plan in PRO_PLANS and status in ACTIVE_STATUSES


def build_user_response(user_data: dict) -> dict:
    """
    Build consistent user response dict with is_pro computed.

    Used by login, register, and /me endpoints to ensure consistent response format.
    """
    if not user_data:
        return None

    return {
        "id": user_data.get("id", ""),
        "email": user_data.get("email"),
        "username": user_data.get("username"),
        "display_name": user_data.get("display_name"),
        "avatar_url": user_data.get("avatar_url"),
        "is_admin": user_data.get("is_admin", False),
        "roles": user_data.get("roles", []),
        "subscription_plan": user_data.get("subscription_plan"),
        "subscription_status": user_data.get("subscription_status"),
        "allowed_languages": user_data.get("allowed_languages"),
        "is_pro": compute_is_pro(user_data),
    }


# =============================================================================
# Token Validation
# =============================================================================

# SECURITY: Token format validation
MAX_TOKEN_LENGTH = 2048  # JWT tokens should not exceed 2KB
TOKEN_PATTERN = re.compile(r'^[\w\-_.]+$')  # Valid JWT characters


def validate_token_format(token: str) -> bool:
    """
    Validate token format before processing.

    SECURITY: Prevents processing of malformed or excessively long tokens.
    """
    if not token:
        return False
    if len(token) > MAX_TOKEN_LENGTH:
        logger.warning(f"Token exceeds maximum length: {len(token)} bytes")
        return False
    if not TOKEN_PATTERN.match(token):
        logger.warning("Token contains invalid characters")
        return False
    return True


# =============================================================================
# Auth Dependencies
# =============================================================================


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Get current user from token via gateway provider."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header",
        )

    token = authorization.split("Bearer ")[1]

    # SECURITY: Validate token format before processing
    if not validate_token_format(token):
        raise HTTPException(
            status_code=401,
            detail="Invalid token format",
        )

    auth_provider = get_auth_provider()
    result = await auth_provider.verify_token(token)

    if not result.ok:
        raise HTTPException(
            status_code=401,
            detail=result.error or "Invalid or expired token",
        )

    return result.user.model_dump() if result.user else {}


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Get current user if token provided, otherwise return None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split("Bearer ")[1]

    # SECURITY: Validate token format
    if not validate_token_format(token):
        logger.warning("Optional auth: invalid token format rejected")
        return None

    auth_provider = get_auth_provider()

    try:
        result = await auth_provider.verify_token(token)
        if result.ok and result.user:
            return result.user.model_dump()
    except Exception as e:
        # SECURITY: Log the exception type (not details) for debugging
        logger.warning(f"Token verification failed: {type(e).__name__}")

    return None
