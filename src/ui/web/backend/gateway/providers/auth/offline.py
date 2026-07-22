"""
Offline Auth Provider

Self-contained authentication for fully offline (no network) desktop mode.
Uses local SQLite database + JWT tokens signed with a local secret.
"""

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

from jose import JWTError, jwt

from gateway.providers.base import AuthProvider, AuthResult, UserInfo
from gateway.storage.offline_db import get_offline_cursor, init_offline_db

logger = logging.getLogger(__name__)

# JWT configuration
_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 60       # 1 hour
_REFRESH_TOKEN_EXPIRE_DAYS = 7          # 7 days
_LEGACY_DEFAULT_ADMIN_ENV = "FLYTO_OFFLINE_ALLOW_DEFAULT_ADMIN"
_TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}

# PBKDF2 configuration
_PBKDF2_ITERATIONS = 260_000
_SALT_LENGTH = 32


def _get_jwt_secret() -> str:
    """Get JWT secret from environment or generate a persistent one."""
    for env_name in ("FLYTO_OFFLINE_AUTH_SECRET", "OFFLINE_JWT_SECRET"):
        secret = os.environ.get(env_name, "").strip()
        if secret:
            if len(secret) < 32:
                raise RuntimeError("FLYTO_OFFLINE_AUTH_SECRET must contain at least 32 characters")
            return secret

    auth_mode = os.environ.get(
        "FLYTO_OFFLINE_LOGIN_MODE",
        os.environ.get("FLYTO_OFFLINE_AUTH_MODE", "none"),
    ).strip().lower()
    api_host = os.environ.get("API_HOST", "127.0.0.1").strip().lower()
    if auth_mode == "jwt" and api_host not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError(
            "FLYTO_OFFLINE_AUTH_SECRET is required when CE JWT auth is exposed beyond loopback"
        )

    # Fall back to a file-based secret so tokens survive restarts
    from gateway.storage.offline_db import get_offline_db_path
    secret_path = get_offline_db_path().with_name(".offline_jwt_secret")
    if secret_path.exists():
        return secret_path.read_text().strip()

    # Generate and persist
    secret_path.parent.mkdir(parents=True, exist_ok=True)
    secret = uuid.uuid4().hex + uuid.uuid4().hex  # 64 hex chars
    secret_path.write_text(secret)
    # Restrict permissions (best-effort on Windows)
    try:
        secret_path.chmod(0o600)
    except OSError:
        pass
    logger.info("Generated new offline JWT secret")
    return secret


def _hash_password(password: str) -> str:
    """
    Hash password using PBKDF2-HMAC-SHA256.

    Returns: salt_hex$hash_hex
    """
    salt = os.urandom(_SALT_LENGTH)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    """
    Verify password against stored salt_hex$hash_hex.

    Returns True if password matches.
    """
    try:
        salt_hex, hash_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def _create_access_token(user_id: str, email: str, roles: list) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm=_ALGORITHM)


def _create_refresh_token(user_id: str) -> str:
    """Create a signed JWT refresh token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm=_ALGORITHM)


def _user_row_to_info(row: dict) -> UserInfo:
    """Convert a database row dict to a UserInfo model."""
    roles = json.loads(row.get("roles") or '["user"]')
    return UserInfo(
        id=row["id"],
        email=row.get("email", ""),
        username=row.get("username", ""),
        display_name=row.get("display_name", ""),
        avatar_url=row.get("avatar_url"),
        roles=roles,
        is_admin=bool(row.get("is_admin", 0)),
        is_active=bool(row.get("is_active", 1)),
        metadata={"provider": "offline"},
    )


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY_ENV_VALUES


def _user_count() -> int:
    with get_offline_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        result = cursor.fetchone()
    return result["cnt"] if result else 0


def offline_setup_required() -> bool:
    """Return True when the offline database has no configured users."""
    return _user_count() == 0


def _ensure_admin_user() -> None:
    """
    Create the legacy default admin user only when explicitly enabled.

    Called once during provider initialization.
    """
    if not offline_setup_required():
        return

    if not _env_truthy(_LEGACY_DEFAULT_ADMIN_ENV):
        logger.info("Offline auth setup required; no default admin user created")
        return

    now = datetime.now(timezone.utc).isoformat()
    admin_id = uuid.uuid4().hex
    password_hash = _hash_password("admin")

    with get_offline_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (id, email, username, display_name, password_hash,
                               roles, is_admin, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                admin_id,
                "admin@localhost",
                "admin",
                "Admin",
                password_hash,
                '["admin", "user"]',
                1,
                1,
                now,
                now,
            ),
        )

    logger.warning(
        "Created default admin user (admin@localhost / admin). "
        "CHANGE THE PASSWORD IMMEDIATELY for security."
    )


class OfflineAuthProvider(AuthProvider):
    """
    Fully offline authentication provider.

    Uses local SQLite for user storage and PyJWT for JWT tokens.
    No network calls required.
    """

    def __init__(self) -> None:
        # Ensure the offline database is initialized
        init_offline_db()
        # Legacy/dev default admin is explicit opt-in only.
        _ensure_admin_user()
        logger.info("OfflineAuthProvider initialized")

    @property
    def provider_name(self) -> str:
        return "offline"

    @property
    def setup_required(self) -> bool:
        """Whether first-run local setup still needs to create the owner."""
        return offline_setup_required()

    def is_setup_required(self) -> bool:
        """Compatibility helper for callers that prefer a method form."""
        return self.setup_required

    async def verify_token(self, token: str) -> AuthResult:
        """
        Verify a JWT access token signed with the local secret.

        Returns AuthResult with user info looked up from the offline database.
        """
        try:
            payload = jwt.decode(token, _get_jwt_secret(), algorithms=[_ALGORITHM])
        except JWTError as e:
            return AuthResult(ok=False, error=f"Invalid token: {e}")

        if payload.get("type") != "access":
            return AuthResult(ok=False, error="Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            return AuthResult(ok=False, error="Token missing subject")

        # Look up user in database
        with get_offline_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

        if not row:
            return AuthResult(ok=False, error="User not found")

        if not row.get("is_active", 1):
            return AuthResult(ok=False, error="Account is deactivated")

        user = _user_row_to_info(row)
        return AuthResult(ok=True, user=user, token=token)

    async def authenticate(self, credentials: Dict[str, Any]) -> AuthResult:
        """
        Authenticate with email + password.

        Args:
            credentials: {"email": "...", "password": "..."}

        Returns:
            AuthResult with JWT access + refresh tokens on success.
        """
        email = credentials.get("email", "").lower().strip()
        password = credentials.get("password", "")

        if not email or not password:
            return AuthResult(ok=False, error="Email and password are required")

        # Look up user by email
        with get_offline_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()

        if not row:
            return AuthResult(ok=False, error="Invalid email or password")

        if not row.get("is_active", 1):
            return AuthResult(ok=False, error="Account is deactivated")

        # Verify password
        if not _verify_password(password, row["password_hash"]):
            return AuthResult(ok=False, error="Invalid email or password")

        user = _user_row_to_info(row)
        roles = json.loads(row.get("roles") or '["user"]')

        access_token = _create_access_token(row["id"], email, roles)
        refresh_token = _create_refresh_token(row["id"])

        return AuthResult(
            ok=True,
            user=user,
            token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, refresh_token: str) -> AuthResult:
        """
        Issue a new access token from a valid refresh token.
        """
        try:
            payload = jwt.decode(refresh_token, _get_jwt_secret(), algorithms=[_ALGORITHM])
        except JWTError as e:
            return AuthResult(ok=False, error=f"Invalid refresh token: {e}")

        if payload.get("type") != "refresh":
            return AuthResult(ok=False, error="Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            return AuthResult(ok=False, error="Token missing subject")

        # Look up user in database
        with get_offline_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

        if not row:
            return AuthResult(ok=False, error="User not found")

        if not row.get("is_active", 1):
            return AuthResult(ok=False, error="Account is deactivated")

        user = _user_row_to_info(row)
        roles = json.loads(row.get("roles") or '["user"]')

        new_access_token = _create_access_token(row["id"], row["email"], roles)
        new_refresh_token = _create_refresh_token(row["id"])

        return AuthResult(
            ok=True,
            user=user,
            token=new_access_token,
            refresh_token=new_refresh_token,
        )

    async def register(self, credentials: Dict[str, Any]) -> AuthResult:
        """
        Register a new user in the offline database.

        Args:
            credentials: {"email": "...", "password": "...", "username": "..."}

        Returns:
            AuthResult with JWT tokens on success.
        """
        email = credentials.get("email", "").lower().strip()
        password = credentials.get("password", "")
        display_name = credentials.get("username", "") or credentials.get("display_name", "")

        if not email or not password:
            return AuthResult(ok=False, error="Email and password are required")

        now = datetime.now(timezone.utc).isoformat()
        user_id = uuid.uuid4().hex
        password_hash = _hash_password(password)
        username = email.split("@")[0]

        # Keep the first-owner decision and insert under one process-wide DB lock.
        # Additional self-registration is explicit opt-in for trusted deployments.
        with get_offline_cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return AuthResult(ok=False, error="Email already registered")

            cursor.execute("SELECT COUNT(*) as cnt FROM users")
            count_result = cursor.fetchone()
            is_first_user = (count_result["cnt"] if count_result else 0) == 0
            if not is_first_user and not _env_truthy("FLYTO_OFFLINE_ALLOW_REGISTRATION"):
                return AuthResult(
                    ok=False,
                    error="Self-registration is disabled after the owner account is created",
                )

            roles = ["admin", "user"] if is_first_user else ["user"]
            roles_json = json.dumps(roles)
            cursor.execute(
                """
                INSERT INTO users (id, email, username, display_name, password_hash,
                                   roles, is_admin, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    email,
                    username,
                    display_name or username,
                    password_hash,
                    roles_json,
                    1 if is_first_user else 0,
                    1,
                    now,
                    now,
                ),
            )

        user = UserInfo(
            id=user_id,
            email=email,
            username=username,
            display_name=display_name or username,
            roles=roles,
            is_admin=is_first_user,
            is_active=True,
            metadata={"provider": "offline"},
        )

        access_token = _create_access_token(user_id, email, roles)
        refresh_token = _create_refresh_token(user_id)

        logger.info(f"New offline user registered: {email}")

        return AuthResult(
            ok=True,
            user=user,
            token=access_token,
            refresh_token=refresh_token,
        )


def validate_offline_auth_configuration() -> None:
    """Fail startup when externally exposed JWT auth has no stable secret."""
    auth_mode = os.environ.get(
        "FLYTO_OFFLINE_LOGIN_MODE",
        os.environ.get("FLYTO_OFFLINE_AUTH_MODE", "none"),
    ).strip().lower()
    if auth_mode == "jwt":
        _get_jwt_secret()
