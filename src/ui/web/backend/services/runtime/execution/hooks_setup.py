"""
Hooks Setup

Creates and configures execution hooks for step tracking and evidence collection.
"""

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.runtime.execution.models import ExecutionInfo

logger = logging.getLogger(__name__)


def create_step_tracking_hooks(
    execution_id: str,
    runs_directory: Optional[Any],
    execution_info: Optional["ExecutionInfo"] = None,
    user_id: Optional[str] = None,
) -> Optional[Any]:
    """
    Create step tracking hooks for execution.

    Args:
        execution_id: Execution identifier
        runs_directory: Directory for storing run artifacts
        execution_info: ExecutionInfo instance for node state tracking
        user_id: User ID for points deduction (None = skip deduction)

    Returns:
        StepTrackingHooks instance or None if creation fails
    """
    try:
        from services.step_tracking_hooks import StepTrackingHooks
        from gateway.storage import ExecutionRepository

        hooks = StepTrackingHooks(
            execution_id=execution_id,
            runs_directory=runs_directory,
            execution_repo=ExecutionRepository,
            execution_info=execution_info,
            user_id=user_id,
        )
        logger.debug(f"Created step tracking hooks for {execution_id}")
        return hooks
    except Exception as e:
        logger.warning(f"Failed to create step tracking hooks: {e}")
        return None


def create_evidence_hooks(
    execution_id: str,
    screenshot_mode: Optional[str] = None,
) -> Optional[Any]:
    """
    Create evidence hooks for debugging features.

    Args:
        execution_id: Execution identifier
        screenshot_mode: Screenshot capture mode ("off", "on_error", "all")

    Returns:
        Evidence hooks instance or None if creation fails
    """
    try:
        from services.evidence_hooks import create_evidence_hooks as _create_evidence_hooks
        return _create_evidence_hooks(execution_id, screenshot_mode=screenshot_mode)
    except Exception as e:
        logger.warning(f"Failed to create evidence hooks: {e}")
        return None


async def _screencast_start(execution_id: str, info: Optional["ExecutionInfo"], context) -> None:
    """Start screencast after browser.launch succeeds."""
    try:
        browser = context.variables.get("browser")
        if browser is None:
            logger.warning(f"[ScreencastHook] browser not found in variables. keys={list(context.variables.keys())}")
            return

        page = getattr(browser, "_page", None) or getattr(browser, "page", None)
        if page is None:
            logger.warning(f"[ScreencastHook] page not found on browser. type={type(browser).__name__} attrs={[a for a in dir(browser) if 'page' in a.lower()]}")
            return

        from services.screencast import get_screencast_manager
        manager = get_screencast_manager()
        await manager.start_screencast(execution_id, page)

        if info:
            info.metadata["has_browser"] = True

        try:
            from services.websocket_manager import manager as ws_manager
            viewport = manager.get_session(execution_id)
            vp = viewport.viewport if viewport else {"width": 1280, "height": 720}
            await ws_manager.send_log(execution_id, {
                "type": "browser_available",
                "has_browser": True,
                "viewport": vp,
            })
        except Exception:
            pass

        logger.info(f"Screencast auto-started for {execution_id}")
    except Exception as e:
        logger.warning(f"Failed to auto-start screencast: {e}")


async def _screencast_stop(execution_id: str, info: Optional["ExecutionInfo"]) -> None:
    """Stop screencast after browser.close."""
    try:
        from services.screencast import get_screencast_manager
        manager = get_screencast_manager()
        await manager.stop_screencast(execution_id)

        if info:
            info.metadata["has_browser"] = False

        try:
            from services.websocket_manager import manager as ws_manager
            await ws_manager.send_log(execution_id, {
                "type": "browser_closed",
                "has_browser": False,
            })
        except Exception:
            pass

        logger.info(f"Screencast auto-stopped for {execution_id}")
    except Exception as e:
        logger.warning(f"Failed to auto-stop screencast: {e}")


async def _screencast_restart(execution_id: str, info: Optional["ExecutionInfo"], context) -> None:
    """Restart screencast when browser page changes (proxy rotate, pool switch, etc.)."""
    try:
        await _screencast_stop(execution_id, info)
        await _screencast_start(execution_id, info, context)
        logger.info(f"Screencast restarted for {execution_id}")
    except Exception as e:
        logger.warning(f"Failed to restart screencast: {e}")


def create_screencast_hooks(
    execution_id: str,
    execution_info: Optional["ExecutionInfo"] = None,
) -> Optional[Any]:
    """
    Create screencast hooks that auto-start/stop CDP screencast on browser.launch/close.

    Detects browser.launch success -> starts screencast streaming.
    Detects browser.close -> stops screencast.
    Sends browser_available/browser_closed events via execution WebSocket.
    """
    try:
        from core.engine.hooks import ExecutorHooks, HookContext, HookResult

        class ScreencastHooks(ExecutorHooks):
            """Auto-starts CDP screencast when browser.launch succeeds."""

            def __init__(self, exec_id: str, info: Optional["ExecutionInfo"]):
                self._execution_id = exec_id
                self._info = info
                self._last_page_id = None

            def on_post_execute(self, context: HookContext) -> HookResult:
                """Handle post-execute to start/stop screencast on browser events."""
                import asyncio
                module_id = context.module_id or ""
                logger.info(f"[ScreencastHook] on_post_execute module_id={module_id} error={context.error}")

                if module_id == "browser.close":
                    logger.info("[ScreencastHook] browser.close detected, stopping screencast")
                    asyncio.ensure_future(_screencast_stop(self._execution_id, self._info))
                    self._last_page_id = None
                    return HookResult.continue_execution()

                # Detect browser page change from ANY module
                browser = context.variables.get("browser")
                if browser:
                    page = getattr(browser, "_page", None)
                    page_id = id(page) if page else None
                    if page_id and page_id != self._last_page_id:
                        if self._last_page_id is not None:
                            logger.info(f"[ScreencastHook] page changed (module={module_id}), restarting screencast")
                            asyncio.ensure_future(_screencast_restart(self._execution_id, self._info, context))
                        else:
                            logger.info("[ScreencastHook] first page detected, starting screencast")
                            asyncio.ensure_future(_screencast_start(self._execution_id, self._info, context))
                        self._last_page_id = page_id

                return HookResult.continue_execution()

        hooks = ScreencastHooks(execution_id, execution_info)
        logger.debug(f"Created screencast hooks for {execution_id}")
        return hooks
    except Exception as e:
        logger.warning(f"Failed to create screencast hooks: {e}")
        return None


def create_credential_resolver_hooks(
    execution_id: str,
    credential_tokens: Dict[str, str],
) -> Optional[Any]:
    """
    Create credential resolver hooks that decrypt secretRef tokens in step params.

    Args:
        execution_id: Execution identifier
        credential_tokens: Dict mapping credential name to token string

    Returns:
        CredentialResolverHooks instance or None if creation fails
    """
    if not credential_tokens:
        return None

    try:
        from core.engine.hooks import ExecutorHooks, HookContext, HookResult

        class CredentialResolverHooks(ExecutorHooks):
            """Resolves secretRef objects in step params before execution."""

            def __init__(self, exec_id: str, tokens: Dict[str, str]):
                """Initialize with execution ID and credential tokens."""
                self._execution_id = exec_id
                self._tokens = tokens

            def on_pre_execute(self, context: HookContext) -> HookResult:
                """Replace secretRef objects with decrypted credential values."""
                if context.params:
                    self._resolve_refs(context.params)
                return HookResult.continue_execution()

            def _resolve_refs(self, obj: Any) -> Any:
                """Recursively replace secretRef objects with decrypted values."""
                if isinstance(obj, dict):
                    if obj.get('type') == 'secretRef':
                        return self._resolve_single_ref(obj)
                    for key in list(obj.keys()):
                        resolved = self._resolve_refs(obj[key])
                        if resolved is not obj[key]:
                            obj[key] = resolved
                elif isinstance(obj, list):
                    for i in range(len(obj)):
                        resolved = self._resolve_refs(obj[i])
                        if resolved is not obj[i]:
                            obj[i] = resolved
                return obj

            def _resolve_single_ref(self, ref: dict) -> Any:
                """Resolve a single secretRef to its decrypted value."""
                credential_name = ref.get('credential_name', '')
                token = self._tokens.get(credential_name)
                if not token:
                    logger.warning(
                        f"No token found for credential '{credential_name}' "
                        f"in execution {self._execution_id}"
                    )
                    return ref

                try:
                    from services.credentials.service import CredentialService
                    value = CredentialService.resolve_execution_token(
                        token=token,
                        execution_id=self._execution_id,
                        single_use=False,
                    )
                    if value is not None:
                        logger.debug(f"Resolved credential '{credential_name}'")
                        return value
                    else:
                        logger.warning(
                            f"Failed to resolve credential '{credential_name}'"
                        )
                        return ref
                except Exception as e:
                    logger.error(
                        f"Error resolving credential '{credential_name}': {e}"
                    )
                    return ref

        hooks = CredentialResolverHooks(execution_id, credential_tokens)
        logger.info(
            f"Created credential resolver hooks for {execution_id} "
            f"with {len(credential_tokens)} credential(s)"
        )
        return hooks
    except Exception as e:
        logger.warning(f"Failed to create credential resolver hooks: {e}")
        return None


def combine_hooks(hooks_list: list) -> Optional[Any]:
    """
    Combine multiple hook instances into a composite hook.

    Args:
        hooks_list: List of hook instances (None values are filtered out)

    Returns:
        CompositeHooks instance or single hook if only one, or None if empty
    """
    # Filter out None values
    valid_hooks = [h for h in hooks_list if h is not None]
    logger.info(f"[HooksSetup] combine_hooks: {len(hooks_list)} input, {len(valid_hooks)} valid")

    if not valid_hooks:
        logger.warning("[HooksSetup] No valid hooks to combine!")
        return None

    if len(valid_hooks) == 1:
        logger.info(f"[HooksSetup] Using single hook: {type(valid_hooks[0]).__name__}")
        return valid_hooks[0]

    try:
        from services.composite_hooks import CompositeHooks
        combined = CompositeHooks(valid_hooks)
        logger.info(f"[HooksSetup] Created composite hooks with {len(valid_hooks)} hook(s)")
        return combined
    except Exception as e:
        logger.warning(f"[HooksSetup] Failed to create composite hooks: {e}")
        # Return first hook as fallback
        return valid_hooks[0]


def setup_execution_hooks(info: "ExecutionInfo") -> Optional[Any]:
    """
    Set up all hooks for an execution.

    This is the main entry point for hook setup. It creates:
    1. Step tracking hooks (for progress and SQLite persistence)
    2. Evidence hooks (for screenshots and debugging)
    3. Credential resolver hooks (for decrypting secretRef tokens)
    4. Combines them into a composite hook

    Args:
        info: ExecutionInfo instance with runs_directory and metadata

    Returns:
        Combined hooks instance or None if all hooks fail to create
    """
    # Create step tracking hooks (pass info for node state tracking)
    step_hooks = create_step_tracking_hooks(
        execution_id=info.execution_id,
        runs_directory=info.runs_directory,
        execution_info=info,
        user_id=getattr(info, "user_id", None) or info.metadata.get("user_id"),
    )
    info.step_hooks = step_hooks

    # Create evidence hooks
    screenshot_mode = info.metadata.get('screenshot_mode')
    evidence_hooks = create_evidence_hooks(
        execution_id=info.execution_id,
        screenshot_mode=screenshot_mode,
    )

    # Create credential resolver hooks
    credential_tokens = info.metadata.get('credential_tokens', {})
    credential_hooks = create_credential_resolver_hooks(
        execution_id=info.execution_id,
        credential_tokens=credential_tokens,
    )

    # Create screencast hooks (auto-start/stop CDP screencast on browser.launch/close)
    screencast_hooks = create_screencast_hooks(
        execution_id=info.execution_id,
        execution_info=info,
    )

    # Combine all hooks
    return combine_hooks([step_hooks, evidence_hooks, credential_hooks, screencast_hooks])
