"""
Shared Webhook Signature Verification

Pure async function for HMAC-SHA256 webhook signature verification.
No framework coupling — callers convert results to their own error format.
"""

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional


@dataclass
class VerificationResult:
    """Result of webhook signature verification."""
    valid: bool
    error: Optional[str] = None
    code: Optional[str] = None


async def verify_webhook_signature(
    secret: str,
    body: bytes,
    signature: str,
    timestamp: str,
    nonce: str,
    tolerance_seconds: int = 300,
    nonce_checker: Optional[Callable[[str], Awaitable[bool]]] = None,
) -> VerificationResult:
    """
    Verify a webhook request's HMAC-SHA256 signature.

    Args:
        secret: Webhook secret key
        body: Raw request body bytes
        signature: X-Signature header value (with or without "sha256=" prefix)
        timestamp: X-Timestamp header value (unix timestamp string)
        nonce: X-Nonce header value (unique per request)
        tolerance_seconds: Max age of timestamp in seconds (default 300 = 5 min)
        nonce_checker: Async callable that returns True if nonce was already used.
                       Accepts NonceStore.exists or provider.check_nonce.

    Returns:
        VerificationResult with valid=True on success, or error details on failure.
    """
    # Check required fields
    if not signature:
        return VerificationResult(valid=False, error="Missing signature", code="NO_SIGNATURE")

    if not timestamp:
        return VerificationResult(valid=False, error="Missing timestamp", code="NO_TIMESTAMP")

    if not nonce:
        return VerificationResult(valid=False, error="Missing nonce", code="NO_NONCE")

    # Verify timestamp (prevent replay)
    try:
        ts = int(timestamp)
        now = int(time.time())
        if abs(now - ts) > tolerance_seconds:
            return VerificationResult(
                valid=False,
                error=f"Timestamp too old (tolerance: {tolerance_seconds}s)",
                code="TIMESTAMP_EXPIRED",
            )
    except ValueError:
        return VerificationResult(valid=False, error="Invalid timestamp", code="INVALID_TIMESTAMP")

    # Check nonce (prevent replay)
    if nonce_checker is not None:
        nonce_used = await nonce_checker(nonce)
        if nonce_used:
            return VerificationResult(valid=False, error="Nonce already used", code="NONCE_REUSED")

    # Verify HMAC-SHA256 signature
    body_str = body.decode("utf-8") if body else ""
    expected_payload = f"{timestamp}.{nonce}.{body_str}"
    expected_sig = hmac.new(
        secret.encode(),
        expected_payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    # Handle sha256= prefix
    provided_sig = signature
    if signature.startswith("sha256="):
        provided_sig = signature[7:]

    if not hmac.compare_digest(expected_sig, provided_sig):
        return VerificationResult(valid=False, error="Invalid signature", code="INVALID_SIGNATURE")

    return VerificationResult(valid=True)


def compute_signature(secret: str, timestamp: str, nonce: str, body: str) -> str:
    """
    Compute webhook signature for testing or client implementations.

    Returns:
        Signature string with "sha256=" prefix.
    """
    payload = f"{timestamp}.{nonce}.{body}"
    sig = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={sig}"
