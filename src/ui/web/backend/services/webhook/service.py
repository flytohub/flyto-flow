"""
Webhook Service

Main service for secure webhook triggering with signature verification.
"""

import logging
import secrets
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from services.webhook.models import Webhook, WebhookStatus, WebhookTriggerResult
from services.webhook.repository import WebhookRepository
from services.webhook.nonce_store import NonceStore

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Webhook service for secure workflow triggering.

    Security features:
    - HMAC-SHA256 signature verification
    - Timestamp validation (prevents replay)
    - Nonce checking (prevents replay)
    - IP allowlist (optional)
    """

    def __init__(
        self,
        execute_workflow: Callable[[str, Dict], Any],
    ):
        """
        Initialize webhook service.

        Args:
            execute_workflow: Function to execute a workflow
        """
        self.execute_workflow = execute_workflow

    async def trigger(
        self,
        webhook_id: str,
        body: bytes,
        signature: Optional[str],
        timestamp: Optional[str],
        nonce: Optional[str],
        client_ip: Optional[str] = None,
    ) -> WebhookTriggerResult:
        """
        Trigger a webhook.

        Args:
            webhook_id: Webhook ID
            body: Request body (raw bytes)
            signature: X-Signature header
            timestamp: X-Timestamp header
            nonce: X-Nonce header
            client_ip: Client IP address

        Returns:
            WebhookTriggerResult with execution ID or error
        """
        # Get webhook
        webhook = WebhookRepository.get(webhook_id)
        if not webhook:
            return WebhookTriggerResult(
                success=False,
                error="Webhook not found",
                error_code="NOT_FOUND",
            )

        # Check status
        if webhook.status != WebhookStatus.ACTIVE:
            return WebhookTriggerResult(
                success=False,
                error="Webhook is disabled",
                error_code="DISABLED",
            )

        # Check IP allowlist
        if webhook.allowed_ips and client_ip:
            if client_ip not in webhook.allowed_ips:
                logger.warning(f"Webhook {webhook_id} blocked IP: {client_ip}")
                return WebhookTriggerResult(
                    success=False,
                    error="IP not allowed",
                    error_code="IP_BLOCKED",
                )

        # Verify security if required
        if webhook.require_signature:
            verification = await self._verify_request(
                webhook=webhook,
                body=body,
                signature=signature,
                timestamp=timestamp,
                nonce=nonce,
            )
            if not verification["valid"]:
                return WebhookTriggerResult(
                    success=False,
                    error=verification["error"],
                    error_code=verification["code"],
                )

        # Parse body and map inputs
        try:
            import json
            payload = json.loads(body.decode("utf-8")) if body else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {}

        inputs = self._map_inputs(payload, webhook.inputs_mapping)

        # Execute workflow
        try:
            result = await self.execute_workflow(webhook.workflow_id, inputs)

            # Record trigger
            WebhookRepository.record_trigger(webhook_id)

            # Store nonce
            if nonce:
                NonceStore.store(nonce, webhook_id)

            return WebhookTriggerResult(
                success=True,
                execution_id=result.get("execution_id"),
            )

        except Exception as e:
            logger.error(f"Webhook execution failed: {e}")
            return WebhookTriggerResult(
                success=False,
                error=str(e),
                error_code="EXECUTION_FAILED",
            )

    async def _verify_request(
        self,
        webhook: Webhook,
        body: bytes,
        signature: Optional[str],
        timestamp: Optional[str],
        nonce: Optional[str],
    ) -> Dict[str, Any]:
        """Verify webhook request security using shared HMAC utility."""
        from services.crypto.webhook_signature import verify_webhook_signature

        async def _nonce_exists(n: str) -> bool:
            return NonceStore.exists(n)

        result = await verify_webhook_signature(
            secret=webhook.secret,
            body=body,
            signature=signature,
            timestamp=timestamp,
            nonce=nonce,
            tolerance_seconds=webhook.timestamp_tolerance_seconds,
            nonce_checker=_nonce_exists,
        )
        if result.valid:
            return {"valid": True}
        return {"valid": False, "error": result.error, "code": result.code}

    def _map_inputs(
        self,
        payload: Dict[str, Any],
        mapping: Dict[str, str],
    ) -> Dict[str, Any]:
        """Map webhook payload to workflow inputs."""
        if not mapping:
            return payload

        result = {}
        for target_key, source_path in mapping.items():
            value = self._get_nested_value(payload, source_path)
            if value is not None:
                result[target_key] = value

        return result

    @staticmethod
    def _get_nested_value(obj: Dict, path: str) -> Any:
        """Get nested value from dict using dot notation."""
        from core.engine.variable_resolver import VariableResolver
        return VariableResolver.get_nested_value(obj, path)

    @staticmethod
    def compute_signature(
        secret: str,
        timestamp: str,
        nonce: str,
        body: str,
    ) -> str:
        """
        Compute signature for webhook request.

        Use this for testing or client implementations.

        Args:
            secret: Webhook secret
            timestamp: Unix timestamp
            nonce: Unique nonce
            body: Request body

        Returns:
            Signature string (sha256=...)
        """
        from services.crypto.webhook_signature import compute_signature
        return compute_signature(secret, timestamp, nonce, body)

    @staticmethod
    async def create_webhook(
        name: str,
        workflow_id: str,
        user_id: Optional[str] = None,
        inputs_mapping: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Webhook:
        """
        Create a new webhook.

        Args:
            name: Webhook name
            workflow_id: Target workflow
            user_id: Owner user
            inputs_mapping: Payload to inputs mapping
            **kwargs: Additional webhook fields

        Returns:
            Created webhook with secret
        """
        webhook = Webhook(
            id=str(uuid4()),
            name=name,
            workflow_id=workflow_id,
            secret=secrets.token_urlsafe(32),
            user_id=user_id,
            inputs_mapping=inputs_mapping or {},
            **kwargs,
        )

        return WebhookRepository.create(webhook)
