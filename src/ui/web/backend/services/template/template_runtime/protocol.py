"""
JSON-RPC Protocol for Template Runtime

Handles encoding/decoding of JSON-RPC messages for template subprocess communication.
Based on flyto-core runtime protocol with template-specific extensions.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Protocol constants
JSONRPC_VERSION = "2.0"
PROTOCOL_VERSION = "0.1.0"


class ErrorCode:
    """Standard JSON-RPC and template-specific error codes."""
    # Standard JSON-RPC errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # Template-specific errors
    TEMPLATE_NOT_FOUND = -32001
    STEP_EXECUTION_FAILED = -32002
    PERMISSION_DENIED = -32003
    SECRET_NOT_PROVIDED = -32004
    TIMEOUT = -32005
    RESOURCE_EXHAUSTED = -32006
    MODULE_NOT_ALLOWED = -32007
    VALIDATION_ERROR = -32008


@dataclass
class JsonRpcRequest:
    """JSON-RPC 2.0 Request object."""
    method: str
    params: Dict[str, Any]
    id: int
    jsonrpc: str = JSONRPC_VERSION

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params,
            "id": self.id,
        })

    @classmethod
    def from_json(cls, data: str) -> "JsonRpcRequest":
        """Deserialize from JSON string."""
        obj = json.loads(data)
        return cls(
            method=obj["method"],
            params=obj.get("params", {}),
            id=obj["id"],
            jsonrpc=obj.get("jsonrpc", JSONRPC_VERSION),
        )


@dataclass
class JsonRpcResponse:
    """JSON-RPC 2.0 Response object."""
    id: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    jsonrpc: str = JSONRPC_VERSION

    def to_json(self) -> str:
        """Serialize to JSON string."""
        obj = {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
        }
        if self.error is not None:
            obj["error"] = self.error
        else:
            obj["result"] = self.result
        return json.dumps(obj)

    @classmethod
    def from_json(cls, data: str) -> "JsonRpcResponse":
        """Deserialize from JSON string."""
        obj = json.loads(data)
        return cls(
            id=obj["id"],
            result=obj.get("result"),
            error=obj.get("error"),
            jsonrpc=obj.get("jsonrpc", JSONRPC_VERSION),
        )

    @property
    def is_error(self) -> bool:
        """Check if response is an error."""
        return self.error is not None

    @property
    def is_success(self) -> bool:
        """Check if response is successful."""
        return self.error is None


@dataclass
class JsonRpcNotification:
    """JSON-RPC 2.0 Notification (no id, no response expected)."""
    method: str
    params: Dict[str, Any]
    jsonrpc: str = JSONRPC_VERSION

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params,
        })

    @classmethod
    def from_json(cls, data: str) -> "JsonRpcNotification":
        """Deserialize from JSON string."""
        obj = json.loads(data)
        return cls(
            method=obj["method"],
            params=obj.get("params", {}),
            jsonrpc=obj.get("jsonrpc", JSONRPC_VERSION),
        )


class ProtocolEncoder:
    """Encodes messages for template worker communication."""

    @staticmethod
    def encode_handshake(
        protocol_version: str,
        execution_id: str,
        request_id: int,
    ) -> str:
        """
        Encode handshake request.

        Args:
            protocol_version: Protocol version
            execution_id: Current execution ID
            request_id: Request ID for correlation

        Returns:
            JSON-RPC request string
        """
        request = JsonRpcRequest(
            method="handshake",
            params={
                "protocolVersion": protocol_version,
                "executionId": execution_id,
            },
            id=request_id,
        )
        return request.to_json()

    @staticmethod
    def encode_execute_template(
        template_id: str,
        definition: Dict[str, Any],
        input_params: Dict[str, Any],
        execution_id: str,
        config: Dict[str, Any],
        request_id: int,
        timeout_ms: int = 300000,
    ) -> str:
        """
        Encode execute_template request.

        Args:
            template_id: Template ID
            definition: Template definition with steps
            input_params: Input parameters
            execution_id: Unique execution ID
            config: Execution configuration
            request_id: Request ID for correlation
            timeout_ms: Timeout in milliseconds

        Returns:
            JSON-RPC request string
        """
        request = JsonRpcRequest(
            method="execute_template",
            params={
                "templateId": template_id,
                "definition": definition,
                "inputParams": input_params,
                "executionId": execution_id,
                "config": config,
                "timeoutMs": timeout_ms,
            },
            id=request_id,
        )
        return request.to_json()

    @staticmethod
    def encode_shutdown(
        reason: str,
        grace_period_ms: int,
        request_id: int,
    ) -> str:
        """
        Encode shutdown request.

        Args:
            reason: Reason for shutdown
            grace_period_ms: Grace period in milliseconds
            request_id: Request ID for correlation

        Returns:
            JSON-RPC request string
        """
        request = JsonRpcRequest(
            method="shutdown",
            params={
                "reason": reason,
                "gracePeriodMs": grace_period_ms,
            },
            id=request_id,
        )
        return request.to_json()

    @staticmethod
    def encode_ping(request_id: int) -> str:
        """
        Encode ping request for health check.

        Args:
            request_id: Request ID for correlation

        Returns:
            JSON-RPC request string
        """
        request = JsonRpcRequest(
            method="ping",
            params={},
            id=request_id,
        )
        return request.to_json()

    @staticmethod
    def encode_resolve_secrets(
        secret_refs: List[str],
        request_id: int,
    ) -> str:
        """
        Encode resolve_secrets request (worker -> runtime).

        Args:
            secret_refs: List of secret reference names
            request_id: Request ID for correlation

        Returns:
            JSON-RPC request string
        """
        request = JsonRpcRequest(
            method="resolve_secrets",
            params={
                "refs": secret_refs,
            },
            id=request_id,
        )
        return request.to_json()


class ProtocolDecoder:
    """Decodes messages from template worker communication."""

    @staticmethod
    def decode_response(data: str) -> JsonRpcResponse:
        """
        Decode JSON-RPC response.

        Args:
            data: JSON string

        Returns:
            JsonRpcResponse object

        Raises:
            json.JSONDecodeError: If invalid JSON
            KeyError: If missing required fields
        """
        return JsonRpcResponse.from_json(data)

    @staticmethod
    def decode_request(data: str) -> JsonRpcRequest:
        """
        Decode JSON-RPC request (for worker-initiated messages).

        Args:
            data: JSON string

        Returns:
            JsonRpcRequest object

        Raises:
            json.JSONDecodeError: If invalid JSON
            KeyError: If missing required fields
        """
        return JsonRpcRequest.from_json(data)

    @staticmethod
    def decode_notification(data: str) -> JsonRpcNotification:
        """
        Decode JSON-RPC notification.

        Args:
            data: JSON string

        Returns:
            JsonRpcNotification object
        """
        return JsonRpcNotification.from_json(data)

    @staticmethod
    def extract_result(response: JsonRpcResponse) -> Dict[str, Any]:
        """
        Extract result from response, normalizing format.

        Args:
            response: JSON-RPC response

        Returns:
            Normalized result dict with 'ok', 'data', 'error' fields
        """
        if response.is_error:
            error = response.error
            return {
                "ok": False,
                "error": {
                    "code": error.get("code", "UNKNOWN_ERROR"),
                    "message": error.get("message", "Unknown error"),
                    "details": error.get("data"),
                },
            }

        result = response.result or {}

        # Result already has 'ok' field - return as-is
        if "ok" in result:
            return result

        # Wrap raw result
        return {
            "ok": True,
            "data": result,
        }

    @staticmethod
    def is_notification(data: str) -> bool:
        """Check if data is a notification (no 'id' field)."""
        try:
            obj = json.loads(data)
            return "id" not in obj and "method" in obj
        except json.JSONDecodeError:
            return False


def create_error_response(
    request_id: int,
    code: int,
    message: str,
    data: Optional[Dict[str, Any]] = None,
) -> JsonRpcResponse:
    """
    Create a JSON-RPC error response.

    Args:
        request_id: Request ID to correlate with
        code: Error code
        message: Error message
        data: Additional error data

    Returns:
        JsonRpcResponse with error
    """
    error = {
        "code": code,
        "message": message,
    }
    if data is not None:
        error["data"] = data

    return JsonRpcResponse(id=request_id, error=error)


def create_success_response(
    request_id: int,
    result: Dict[str, Any],
) -> JsonRpcResponse:
    """
    Create a JSON-RPC success response.

    Args:
        request_id: Request ID to correlate with
        result: Result data

    Returns:
        JsonRpcResponse with result
    """
    return JsonRpcResponse(id=request_id, result=result)
