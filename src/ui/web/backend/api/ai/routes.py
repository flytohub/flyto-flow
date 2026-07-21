"""
AI Chat API Routes — thin FastAPI wrapper.

Delegates chat logic to flyto-ai Agent + flyto-ai session management.
Cloud-specific concerns (auth, BYOK config, moat) stay here.
"""
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from flyto_ai import Agent, AgentConfig, ChatMessage, ChatRequest, ChatResponse
from flyto_ai.session import SessionStore
from flyto_ai.tools.core_tools import dispatch_core_tool, get_core_tool_defs
from flyto_ai.tools.blueprint_tools import dispatch_blueprint_tool, get_blueprint_tool_defs
from flyto_ai.tools.inspect_page import INSPECT_PAGE_TOOL, dispatch_inspect_page
from api.ai.compose_tool import COMPOSE_WORKFLOW_TOOL, dispatch_compose_workflow

from api.ai import moat_client
from api.auth import get_current_user
from gateway.providers.ai import configured_ai_base_url_allowed
from gateway.providers.data.models import AIUsageRecordDTO
from gateway.providers.hub import get_data_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])

AI_QUOTA_MIN_TOKENS = 256
AI_QUOTA_MAX_RESERVED_OUTPUT = 4096

# ── Session store ────────────────────────────────────────────────────────

_sessions = SessionStore()


# ── Tool aggregation ─────────────────────────────────────────────────────

def _get_all_tools() -> List[Dict]:
    """Aggregate core + inspect_page + blueprint + compose tool definitions."""
    return get_core_tool_defs() + [INSPECT_PAGE_TOOL, COMPOSE_WORKFLOW_TOOL] + get_blueprint_tool_defs()


def _get_core_manifest(include_tools: bool = True, include_categories: bool = True) -> Dict[str, Any]:
    """Return flyto-core MCP manifest without making routes.py import-fragile."""
    try:
        from flyto_ai.tools.core_tools import get_core_capability_manifest
    except ImportError:
        return {
            "ok": False,
            "source": "flyto-core",
            "error": "flyto-ai core manifest support is unavailable",
        }
    return get_core_capability_manifest(
        include_tools=include_tools,
        include_categories=include_categories,
    )


async def _dispatch_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a tool call to the appropriate handler."""
    core_names = {t["name"] for t in get_core_tool_defs()}
    blueprint_names = {t["name"] for t in get_blueprint_tool_defs()}

    if name in core_names:
        return await dispatch_core_tool(name, arguments)
    elif name == "inspect_page":
        return await dispatch_inspect_page(name, arguments)
    elif name == "compose_workflow":
        return await dispatch_compose_workflow(arguments)
    elif name in blueprint_names:
        return await dispatch_blueprint_tool(name, arguments)
    return {"ok": False, "error": "Unknown tool: {}".format(name)}


# ── Helpers ──────────────────────────────────────────────────────────────

def _get_module_count() -> int:
    """Return total available module count, defaulting to 300 on error."""
    try:
        from core.mcp_handler import list_modules
        result = list_modules()
        categories = result.get("categories", [])
        return sum(c.get("count", 0) for c in categories)
    except Exception:
        return 300


def _is_chat_base_url_allowed(
    provider: str,
    base_url: str,
    policies: Dict[str, Any],
) -> bool:
    if not base_url:
        return True
    if provider != "openai-compatible":
        return False
    return configured_ai_base_url_allowed(
        base_url,
        allowed_domains=policies.get("allowed_domains", []),
    )


def _estimate_tokens(text: Any) -> int:
    """Cheap token estimate for quota reservation. Biased high, never zero."""
    if text is None:
        return 0
    value = text if isinstance(text, str) else str(text)
    if not value:
        return 0
    return max(1, (len(value) + 3) // 4)


def _estimate_chat_input_tokens(request: ChatRequest) -> int:
    total = _estimate_tokens(request.message)
    if request.history:
        for msg in request.history:
            total += _estimate_tokens(getattr(msg, "content", ""))
    if request.template_context:
        try:
            total += _estimate_tokens(json.dumps(request.template_context, sort_keys=True))
        except Exception:
            total += _estimate_tokens(request.template_context)
    return max(AI_QUOTA_MIN_TOKENS, total)


def _ai_usage_control_metadata(
    *,
    status: str,
    tokens_needed: int,
    input_tokens: int,
    output_tokens: int,
    reason: str = "",
) -> Dict[str, Any]:
    """Digest-safe BYOK AI control-plane metadata for audit logs."""
    return {
        "control_status": status,
        "action": "ai.chat",
        "meter": "ai.tokens",
        "byok": True,
        "reservation": True,
        "tokens_needed": tokens_needed,
        "input_tokens_estimated": input_tokens,
        "output_tokens_reserved": output_tokens,
        **({"reason": reason} if reason else {}),
    }


async def _record_ai_usage_audit(ai_usage: Any, record: AIUsageRecordDTO) -> None:
    """Best-effort audit-only write for denied/unavailable BYOK AI gates."""
    recorder = getattr(ai_usage, "record_audit_log", None)
    if not callable(recorder):
        return
    try:
        await recorder(record)
    except Exception:
        logger.warning("AI usage audit log write failed", exc_info=True)


async def _reserve_ai_usage(
    user_id: str,
    model: str,
    request: ChatRequest,
    max_tokens: int,
) -> None:
    """Fail-closed cloud-side AI usage gate.

    This endpoint uses BYOK, so provider-reported usage may not be available
    consistently. Reserve an estimated amount before dispatch so failed control
    plane writes cannot create untracked AI/tool execution.
    """
    input_tokens = _estimate_chat_input_tokens(request)
    output_tokens = max(1, min(max_tokens or AI_QUOTA_MAX_RESERVED_OUTPUT, AI_QUOTA_MAX_RESERVED_OUTPUT))
    tokens_needed = input_tokens + output_tokens
    control_metadata = _ai_usage_control_metadata(
        status="allowed",
        tokens_needed=tokens_needed,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    data = None
    try:
        data = get_data_provider()
        allowed = await data.ai_usage.check_quota(user_id, tokens_needed)
        if not allowed:
            denied_metadata = _ai_usage_control_metadata(
                status="quota_exceeded",
                tokens_needed=tokens_needed,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                reason="monthly_ai_token_quota",
            )
            await _record_ai_usage_audit(data.ai_usage, AIUsageRecordDTO(
                user_id=user_id,
                model=model or "unknown",
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                request_type="ai.chat.quota_exceeded",
                metadata=denied_metadata,
            ))
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "quota_exceeded",
                    "action": "ai.chat",
                    "meter": "ai.tokens",
                    "tokens_needed": tokens_needed,
                    "control_status": "quota_exceeded",
                },
            )
        await data.ai_usage.record_usage(AIUsageRecordDTO(
            user_id=user_id,
            model=model or "unknown",
            tokens_input=input_tokens,
            tokens_output=output_tokens,
            request_type="ai.chat.reserve",
            metadata=control_metadata,
        ))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("AI usage reservation failed; blocking chat", exc_info=exc)
        unavailable_metadata = _ai_usage_control_metadata(
            status="unavailable",
            tokens_needed=tokens_needed,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reason=exc.__class__.__name__,
        )
        if data is not None:
            await _record_ai_usage_audit(data.ai_usage, AIUsageRecordDTO(
                user_id=user_id,
                model=model or "unknown",
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                request_type="ai.chat.control_unavailable",
                metadata=unavailable_metadata,
            ))
        raise HTTPException(
            status_code=503,
            detail={
                "error": "ai_control_unavailable",
                "action": "ai.chat",
                "meter": "ai.tokens",
                "control_status": "unavailable",
            },
        ) from exc


# ── Main chat endpoint ───────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    authorization: str = Header(""),
):
    """Chat with AI assistant using BYOK (Bring Your Own Key)."""
    user_id = current_user["id"]
    session_id = request.session_id or uuid.uuid4().hex[:16]

    auth_token = ""
    if authorization.startswith("Bearer "):
        auth_token = authorization.split("Bearer ", 1)[1]

    if request.history and len(request.history) > 50:
        return ChatResponse(
            ok=False, message="History too long. Maximum 50 messages.",
            session_id=session_id, error="history_too_long",
        )

    _sessions.cleanup()

    # Session ownership check
    owner = _sessions.get_owner(session_id)
    if owner is not None and owner != user_id:
        return ChatResponse(
            ok=False, message="Session not found.",
            session_id=session_id, error="session_not_found",
        )

    if not _sessions.exists(session_id):
        _sessions.create(session_id, user_id)

    lock = _sessions.get_lock(session_id)
    async with lock:
        return await _handle_chat(request, user_id, session_id, auth_token)


async def _handle_chat(
    request: ChatRequest,
    user_id: str,
    session_id: str,
    auth_token: str,
) -> ChatResponse:
    """Core chat logic, called under per-session lock."""
    # Load user's AI config
    ai_config = await moat_client.fetch_user_config(auth_token, user_id)
    provider = ai_config.get("provider", "")
    api_key = ai_config.get("api_key", "")
    model = ai_config.get("model", "")
    temperature = ai_config.get("temperature", 0.7)
    max_tokens = ai_config.get("max_tokens", 4096)
    base_url = ai_config.get("base_url", "")

    # Load policies
    policies = await moat_client.get_policies(auth_token)

    if not _is_chat_base_url_allowed(provider, base_url, policies):
        return ChatResponse(
            ok=False,
            message=(
                "Base URL not allowed. Select an OpenAI-compatible provider and "
                "use an endpoint permitted by the deployment policy."
            ),
            session_id=session_id,
            error="invalid_base_url",
        )

    if not api_key:
        return ChatResponse(
            ok=False,
            message="No AI provider available. Please configure your API key in Settings > AI Assistant.",
            session_id=session_id,
            error="no_provider_available",
        )

    await _reserve_ai_usage(user_id, model, request, int(max_tokens or 0))

    # Build message history
    if request.history:
        history = [{"role": m.role, "content": m.content} for m in request.history]
    else:
        history = [{"role": m.role, "content": m.content} for m in _sessions.get_messages(session_id)]

    # Build system prompt
    module_count = _get_module_count()

    reply_language = None
    try:
        from flyto_ai.prompt.system_prompt import detect_language
        reply_language = detect_language(request.message)
    except ImportError:
        pass

    system_prompt = await moat_client.get_system_prompt(
        module_count, auth_token, request.template_context, reply_language,
    )

    # Resolve provider name for Agent
    agent_provider = provider
    if provider == "openai-compatible":
        agent_provider = "openai"

    config = AgentConfig(
        provider=agent_provider,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        base_url=base_url or None,
    )

    agent = Agent(
        config=config,
        tools=_get_all_tools(),
        dispatch_fn=_dispatch_tool,
        system_prompt=system_prompt,
        policies=policies,
    )

    result = await agent.chat(
        message=request.message,
        history=history,
        template_context=request.template_context,
    )

    # Store in session
    _sessions.append(session_id, ChatMessage(role="user", content=request.message))
    _sessions.append(session_id, ChatMessage(role="assistant", content=result.message))

    return ChatResponse(
        ok=result.ok,
        message=result.message,
        session_id=session_id,
        tool_calls=result.tool_calls,
        provider=result.provider,
        model=result.model,
        error=result.error,
        pending_input=result.pending_input,
    )


# ── Health endpoint ──────────────────────────────────────────────────────

@router.get("/health")
async def ai_health(authorization: Optional[str] = Header(None)):
    """Check AI service availability."""
    user_id = None
    auth_token = ""
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split("Bearer ", 1)[1]
        try:
            from gateway.providers.hub import get_auth_provider
            auth_provider = get_auth_provider()
            result = await auth_provider.verify_token(auth_token)
            if result.ok and result.user:
                user_id = result.user.id
        except Exception:
            pass

    if not user_id:
        return {
            "ok": False, "configured": False, "primary": None, "model": "",
            "message": "Not authenticated. Log in to use AI features.",
        }

    try:
        ai_config = await moat_client.fetch_user_config(auth_token, user_id)
    except Exception:
        ai_config = {}

    configured_provider = ai_config.get("provider", "")
    has_key = bool(ai_config.get("api_key", ""))
    available = has_key and configured_provider in ("openai", "anthropic", "openai-compatible")

    return {
        "ok": available, "configured": available,
        "primary": configured_provider if available else None,
        "model": ai_config.get("model", ""),
        "message": "AI ready" if available else "No AI providers available. Configure your API key in Settings.",
    }


@router.get("/tools/manifest")
async def ai_tools_manifest(
    include_tools: bool = Query(True, description="Include per-tool MCP metadata"),
    include_categories: bool = Query(True, description="Include flyto-core module category counts"),
    current_user: dict = Depends(get_current_user),
):
    """Return the flyto-core MCP capability manifest for authenticated cloud UIs."""
    _ = current_user
    return _get_core_manifest(
        include_tools=include_tools,
        include_categories=include_categories,
    )


# ── Session management ──────────────────────────────────────────────────

@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Clear a chat session."""
    user_id = current_user["id"]
    _sessions.delete(session_id, user_id)
    return {"ok": True, "message": "Session cleared"}


# ── Suggestions ──────────────────────────────────────────────────────────

@router.get("/suggestions")
async def get_suggestions(
    context: Optional[str] = Query(None, description="Current context for suggestions"),
    limit: int = Query(5, ge=1, le=20, description="Number of suggestions"),
    current_user: dict = Depends(get_current_user),
):
    """Get workflow suggestions (static defaults)."""
    suggestions = [
        {"title": "Web Scraping", "description": "Extract data from websites", "category": "data"},
        {"title": "File Processing", "description": "Read and transform files", "category": "file"},
        {"title": "API Integration", "description": "Connect to external APIs", "category": "api"},
        {"title": "Image Processing", "description": "Resize, compress, or convert images", "category": "image"},
        {"title": "Text Transformation", "description": "Format, parse, or translate text", "category": "string"},
    ]
    return {"ok": True, "suggestions": suggestions[:limit]}
