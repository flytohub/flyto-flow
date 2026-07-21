"""
Password reset flow: forgot-password, verify-reset-code, reset-password.
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from gateway.providers.hub import get_auth_provider

from .deps import (
    ForgotPasswordRequest,
    VerifyResetCodeRequest,
    ResetPasswordRequest,
    password_reset_rate_limiter,
    mask_email,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, request: Request):
    """
    Initiate password reset - send reset code to email.

    SECURITY: Rate limited to prevent abuse.
    Always returns success to prevent email enumeration.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"reset:{data.email.lower()}:{client_ip}"

    # Check rate limit
    if password_reset_rate_limiter.is_locked(rate_key):
        remaining = password_reset_rate_limiter.get_lockout_remaining(rate_key)
        raise HTTPException(
            status_code=429,
            detail=f"Too many reset attempts. Please try again in {remaining // 60} minutes.",
            headers={"Retry-After": str(remaining)},
        )

    # Record attempt
    password_reset_rate_limiter.record_attempt(rate_key)

    try:
        auth_provider = get_auth_provider()

        if hasattr(auth_provider, 'send_password_reset'):
            await auth_provider.send_password_reset(data.email)
        else:
            raise HTTPException(status_code=501, detail="Password reset not supported")

        logger.info(f"Password reset sent for: {mask_email(data.email)}")
        return {
            "ok": True,
            "message": "If an account exists with this email, a password reset link has been sent.",
        }

    except HTTPException:
        raise
    except ValueError as e:
        error_msg = str(e)
        if "EMAIL_NOT_FOUND" in error_msg:
            # SECURITY: Return same success response to prevent email enumeration
            logger.info(f"Password reset for non-existent email: {mask_email(data.email)}")
            return {
                "ok": True,
                "message": "If an account exists with this email, a password reset link has been sent.",
            }
        logger.error(f"Password reset error for {mask_email(data.email)}: {e}")
        raise HTTPException(status_code=400, detail="Failed to send reset email")
    except Exception as e:
        logger.error(f"Password reset error for {mask_email(data.email)}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/verify-reset-code")
async def verify_reset_code(data: VerifyResetCodeRequest):
    """
    Verify password reset code (Firebase oobCode) is valid.

    Returns the associated email if the code is valid.
    """
    try:
        auth_provider = get_auth_provider()

        if hasattr(auth_provider, 'verify_reset_code'):
            result = await auth_provider.verify_reset_code(data.code)
            return {"ok": True, "valid": True, "email": result.get("email", "")}

        return {"ok": True, "valid": True}

    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"Reset code verification failed: {error_msg}")
        return {"ok": False, "valid": False, "error": "Invalid or expired reset link"}
    except Exception as e:
        logger.error(f"Reset code verification error: {e}")
        return {"ok": False, "valid": False, "error": "Invalid or expired reset link"}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """
    Reset password using Firebase oobCode.

    SECURITY: oobCode is consumed by Firebase after successful reset.
    """
    try:
        auth_provider = get_auth_provider()

        if hasattr(auth_provider, 'reset_password_with_code'):
            result = await auth_provider.reset_password_with_code(
                code=data.code,
                new_password=data.new_password,
            )

            if result:
                logger.info("Password reset successful")
                return {"ok": True, "message": "Password has been reset successfully."}
            else:
                raise HTTPException(status_code=400, detail="Invalid or expired reset link")

        raise HTTPException(
            status_code=501,
            detail="Password reset not supported by this auth provider.",
        )

    except HTTPException:
        raise
    except ValueError as e:
        error_msg = str(e)
        if "EXPIRED_OOB_CODE" in error_msg or "INVALID_OOB_CODE" in error_msg:
            raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")
        if "WEAK_PASSWORD" in error_msg:
            raise HTTPException(status_code=400, detail="Password is too weak")
        logger.error(f"Password reset error: {e}")
        raise HTTPException(status_code=400, detail="Failed to reset password")
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(status_code=400, detail="Failed to reset password")
