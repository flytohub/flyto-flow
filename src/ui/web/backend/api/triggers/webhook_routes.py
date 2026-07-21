"""
Webhook endpoints and maintenance.

All routes are registered on webhook_router (no prefix — cloud_router adds /triggers).
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from gateway.exceptions import ProviderException

from api.auth import get_current_user
from api.errors import forbidden, internal_error, not_found, unauthorized
from services.webhook.models import Webhook, WebhookStatus, WebhookTriggerResult

from .models import (
    CreateWebhookRequest,
    WebhookResponse,
    WebhookWithSecretResponse,
)
from ._helpers import (
    _get_webhook_provider,
    get_webhook_url,
    _verify_webhook_owner,
)
from services.audit.crud_logger import log_crud

logger = logging.getLogger(__name__)

webhook_router = APIRouter()


# ============================================================================
# Webhook Endpoints
# ============================================================================


@webhook_router.post("/webhooks", response_model=WebhookWithSecretResponse)
async def create_webhook(
    request: CreateWebhookRequest,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create a new webhook.

    Returns the webhook including the secret (only shown once).
    Store the secret securely - it cannot be retrieved later.
    """
    workflow_name = ""
    try:
        from gateway.providers.hub import get_data_provider

        workflow = await get_data_provider().workflows.get_workflow(
            user_id=current_user["id"],
            workflow_id=request.workflow_id,
            include_graph=False,
        )
        if workflow:
            workflow_name = workflow.name
    except Exception:
        pass

    try:
        provider = _get_webhook_provider()
        webhook_data = await provider.create({
            "name": request.name,
            "workflow_id": request.workflow_id,
            "workflow_name": workflow_name,
            "user_id": current_user["id"],
            "workspace_id": request.workspace_id,
            "inputs_mapping": request.inputs_mapping,
            "require_signature": request.require_signature,
            "allowed_ips": request.allowed_ips,
            "provider": request.provider,
            "description": request.description,
        })

        webhook = Webhook.from_dict(webhook_data)
        data = webhook.to_dict(include_secret=True)
        data["trigger_url"] = get_webhook_url(webhook.id)

        log_crud("create", "webhook", webhook.id, current_user)

        return data

    except ProviderException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        internal_error(str(e))


@webhook_router.get("/webhooks")
async def list_webhooks(
    workflow_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """List webhooks (secrets not included) with pre-computed counts."""
    provider = _get_webhook_provider()
    webhook_dicts = await provider.list_webhooks(
        user_id=current_user["id"],
        workflow_id=workflow_id,
    )

    enabled_count = 0
    disabled_count = 0
    result = []
    for wd in webhook_dicts:
        webhook = Webhook.from_dict(wd)
        if webhook.status == WebhookStatus.ACTIVE:
            enabled_count += 1
        elif webhook.status == WebhookStatus.DISABLED:
            disabled_count += 1

        data = webhook.to_dict(include_secret=False)
        data["trigger_url"] = get_webhook_url(webhook.id)
        result.append(data)

    return {
        "ok": True,
        "webhooks": result,
        "enabled_count": enabled_count,
        "disabled_count": disabled_count,
        "total_count": len(result),
    }


@webhook_router.get("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get webhook by ID (secret not included)."""
    provider = _get_webhook_provider()
    data = await provider.get(webhook_id)
    if not data:
        not_found("Webhook not found")

    _verify_webhook_owner(data, current_user["id"])
    webhook = Webhook.from_dict(data)
    result = webhook.to_dict(include_secret=False)
    result["trigger_url"] = get_webhook_url(webhook.id)
    return result


@webhook_router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Delete a webhook."""
    provider = _get_webhook_provider()
    data = await provider.get(webhook_id)
    if not data:
        not_found("Webhook not found")
    _verify_webhook_owner(data, current_user["id"])

    await provider.delete(webhook_id)

    log_crud("delete", "webhook", webhook_id, current_user)

    return {"ok": True, "deleted": webhook_id}


@webhook_router.post("/webhooks/{webhook_id}/regenerate-secret")
async def regenerate_webhook_secret(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Regenerate webhook secret. The old secret will no longer work."""
    provider = _get_webhook_provider()
    data = await provider.get(webhook_id)
    if not data:
        not_found("Webhook not found")
    _verify_webhook_owner(data, current_user["id"])

    new_secret = await provider.regenerate_secret(webhook_id)
    return {"ok": True, "secret": new_secret}


@webhook_router.post("/webhooks/{webhook_id}/disable")
async def disable_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Disable a webhook."""
    provider = _get_webhook_provider()
    data = await provider.get(webhook_id)
    if not data:
        not_found("Webhook not found")
    _verify_webhook_owner(data, current_user["id"])

    await provider.update(webhook_id, status="disabled")
    return {"ok": True, "status": "disabled"}


@webhook_router.post("/webhooks/{webhook_id}/enable")
async def enable_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Enable a webhook."""
    provider = _get_webhook_provider()
    data = await provider.get(webhook_id)
    if not data:
        not_found("Webhook not found")
    _verify_webhook_owner(data, current_user["id"])

    await provider.update(webhook_id, status="active")
    return {"ok": True, "status": "active"}


async def _execute_webhook_workflow(
    workflow_id: str,
    inputs: Dict,
    user_id: str,
) -> Dict:
    """Execute a webhook workflow through the active deployment provider."""
    from gateway.providers.hub import get_data_provider

    execution = await get_data_provider().workflows.execute_workflow(
        user_id=user_id,
        workflow_id=workflow_id,
        params=inputs,
    )
    return {"execution_id": execution.id, "status": execution.status}


def _map_webhook_inputs(payload: dict, inputs_mapping: dict) -> dict:
    """Map webhook payload to workflow inputs using dot-path mapping."""
    if not inputs_mapping:
        return payload
    mapped = {}
    for target_key, source_path in inputs_mapping.items():
        current = payload
        for part in source_path.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = None
                break
        if current is not None:
            mapped[target_key] = current
    return mapped


@webhook_router.post("/webhooks/{webhook_id}/trigger")
async def trigger_webhook(
    webhook_id: str,
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
    x_nonce: Optional[str] = Header(None, alias="X-Nonce"),
) -> Dict[str, Any]:
    """
    Trigger a webhook.

    Required headers for signed webhooks:
    - X-Signature: HMAC-SHA256 signature (sha256=...)
    - X-Timestamp: Unix timestamp
    - X-Nonce: Unique nonce (UUID)

    Signature is computed as: HMAC-SHA256(secret, "{timestamp}.{nonce}.{body}")
    """
    provider = _get_webhook_provider()
    webhook_data = await provider.get(webhook_id)
    if not webhook_data:
        not_found("Webhook not found")

    webhook = Webhook.from_dict(webhook_data)
    owner_user_id = webhook.user_id or "system"

    body = await request.body()
    client_ip = request.client.host if request.client else None

    if webhook.status != WebhookStatus.ACTIVE:
        forbidden("Webhook is disabled")

    # Check IP allowlist
    if webhook.allowed_ips and client_ip:
        if client_ip not in webhook.allowed_ips:
            logger.warning(f"Webhook {webhook_id} blocked IP: {client_ip}")
            unauthorized("IP not allowed")

    # Verify signature if required
    if webhook.require_signature:
        from services.crypto.webhook_signature import verify_webhook_signature

        result = await verify_webhook_signature(
            secret=webhook.secret,
            body=body,
            signature=x_signature,
            timestamp=x_timestamp,
            nonce=x_nonce,
            tolerance_seconds=webhook.timestamp_tolerance_seconds,
            nonce_checker=provider.check_nonce,
        )
        if not result.valid:
            unauthorized(result.error)

    # Parse body and map inputs
    try:
        import json
        payload = json.loads(body.decode("utf-8")) if body else {}
    except Exception:
        payload = {}

    inputs = _map_webhook_inputs(payload, webhook.inputs_mapping)

    try:
        result = await _execute_webhook_workflow(webhook.workflow_id, inputs, owner_user_id)

        # Record trigger + store nonce in Firestore
        await provider.record_trigger(webhook_id)
        if x_nonce:
            await provider.store_nonce(x_nonce, webhook_id)

        return WebhookTriggerResult(
            success=True,
            execution_id=result.get("execution_id"),
        ).to_dict()

    except ProviderException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except Exception as e:
        logger.error(f"Webhook execution failed: {e}")
        internal_error(str(e))


# ============================================================================
# Maintenance
# ============================================================================


@webhook_router.post("/nonces/cleanup")
async def cleanup_nonces() -> Dict[str, Any]:
    """
    Clean up expired nonces (maintenance endpoint).

    Note: With Firestore TTL policy, this is largely automatic.
    This endpoint is kept for manual cleanup and backward compatibility.
    """
    try:
        count = await _get_webhook_provider().cleanup_expired_nonces(limit=500)
        return {"ok": True, "cleaned": count}
    except Exception as e:
        logger.warning(f"Nonce cleanup failed: {e}")
        return {"ok": True, "cleaned": 0}
