"""
AI Agent API Routes

Provides endpoints for autonomous AI agent execution.
Uses local BYOK (Bring Your Own Key) AI configuration.
"""
import asyncio
import logging
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/agent")


# ============================================
# Pydantic Models
# ============================================

class AgentExecuteRequest(BaseModel):
    """Request to start agent execution"""
    goal: str = Field(..., description="Goal/task for the agent to accomplish")
    provider: str = Field(default="openai", description="LLM provider")
    model: str = Field(default="gpt-4o", description="Model ID")
    temperature: float = Field(default=0.7, ge=0, le=2)
    tools_allowed: List[str] = Field(default=["browser.*", "file.*"])
    max_iterations: int = Field(default=20, ge=1, le=50)
    system_prompt: Optional[str] = Field(default=None)
    context: Optional[Dict[str, Any]] = Field(default=None)


class AgentExecuteResponse(BaseModel):
    """Response from starting agent execution"""
    ok: bool
    execution_id: str
    message: str


class AgentStatusResponse(BaseModel):
    """Agent execution status"""
    ok: bool
    execution_id: str
    state: str
    iteration: int
    max_iterations: int
    llm_calls: int
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]
    final_output: Optional[Any]


class ToolInfo(BaseModel):
    """Tool/module information"""
    id: str
    name: str
    description: str
    category: str


class ToolsResponse(BaseModel):
    """Available tools response"""
    ok: bool
    tools: List[ToolInfo]
    categories: List[Dict[str, str]]


# ============================================
# In-Memory Execution Store
# ============================================

# Store active and completed executions
_executions: Dict[str, Dict[str, Any]] = {}


def _get_execution(execution_id: str) -> Dict[str, Any]:
    """Get execution by ID or raise 404"""
    if execution_id not in _executions:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    return _executions[execution_id]


# ============================================
# Tool Categories
# ============================================

TOOL_CATEGORIES = [
    {"id": "browser.*", "name": "Browser Automation", "description": "Web browser control"},
    {"id": "file.*", "name": "File Operations", "description": "File read/write/manage"},
    {"id": "http.*", "name": "HTTP Requests", "description": "Make HTTP/API calls"},
    {"id": "code.*", "name": "Code Execution", "description": "Run JavaScript/Python code"},
    {"id": "ai.*", "name": "AI/LLM", "description": "AI model inference"},
    {"id": "data.*", "name": "Data Processing", "description": "Data transformation"},
    {"id": "form.*", "name": "Form Input", "description": "User form input handling"},
]


# ============================================
# Agent Execution Logic
# ============================================

async def _call_flyto_pro_chat(
    message: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Stub — VPS dependency removed. Agent chat requires BYOK AI configuration.
    """
    return {
        "ok": False,
        "error": "Agent chat is not available. Configure your AI provider in Settings > AI Assistant.",
    }


async def _execute_workflow_locally(
    workflow_yaml: str,
    variables: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Execute workflow locally using flyto-core's WorkflowEngine.
    """
    try:
        from services.runtime.execution_manager import get_execution_manager
        manager = get_execution_manager()

        execution_id = await manager.start(
            workflow_yaml=workflow_yaml,
            variables=variables or {},
            workflow_id=None,
            user_id=None,
        )

        # Wait for execution to complete (with timeout)
        max_wait = 60  # 1 minute
        waited = 0
        while waited < max_wait:
            status = manager.get_status(execution_id)
            if status:
                exec_status = status.get("status", "")
                if waited % 2 == 0:  # Log every 2 seconds
                    logger.debug(f"[Exec {execution_id[:8]}] status={exec_status}, waited={waited}s")
                # Check for terminal states (success, completed, failed, cancelled, error)
                if exec_status in ["success", "completed", "failed", "cancelled", "error"]:
                    is_success = exec_status in ["success", "completed"]
                    result = {
                        "ok": is_success,
                        "execution_id": execution_id,
                        "status": exec_status,
                        "result": status.get("result_data") or status.get("result"),
                        "error": status.get("error_message") or status.get("error"),
                    }
                    logger.debug(f"[Exec {execution_id[:8]}] COMPLETED: ok={is_success}, status={exec_status}")
                    return result
            else:
                logger.debug(f"[Exec {execution_id[:8]}] No status found yet, waited={waited}s")
            await asyncio.sleep(0.5)
            waited += 0.5

        logger.error(f"[Exec {execution_id[:8]}] TIMEOUT after {max_wait}s")
        return {"ok": False, "error": "Execution timeout"}

    except Exception as e:
        logger.error(f"Local execution failed: {e}")
        return {"ok": False, "error": str(e)}


async def _run_agent(execution_id: str, request: AgentExecuteRequest):
    """
    Run the agent loop in background.

    Dual-AI Architecture:
    1. THINK: Call flyto-pro /api/chat to get workflow suggestions
    2. ACT: Execute workflow locally using flyto-core
    3. CHECK: Validate result and decide next action
    4. LOOP: Repeat until goal achieved or max iterations
    """
    logger.debug(f"[Agent {execution_id[:8]}] Starting agent execution...")

    execution = _executions.get(execution_id)
    if not execution:
        logger.error(f"[Agent {execution_id[:8]}] Execution not found in _executions!")
        return

    session_id = f"agent-{execution_id[:8]}"

    try:
        execution["state"] = "initializing"
        execution["started_at"] = datetime.now().isoformat()
        logger.debug(f"[Agent {execution_id[:8]}] Initialized, starting iterations...")

        for iteration in range(1, request.max_iterations + 1):
            execution["iteration"] = iteration

            # =========================================
            # THINK: Get workflow suggestions from flyto-pro
            # =========================================
            execution["state"] = "thinking"
            execution["llm_calls"] = execution.get("llm_calls", 0) + 1

            # Build message with context from previous iterations
            message = request.goal
            if iteration > 1 and execution.get("last_result"):
                last_result = execution["last_result"]
                if last_result.get("ok"):
                    message = f"Previous step succeeded with result: {last_result.get('result', {})}. Continue with: {request.goal}"
                else:
                    message = f"Previous step failed with error: {last_result.get('error', 'unknown')}. Try a different approach for: {request.goal}"

            chat_result = await _call_flyto_pro_chat(
                message=message,
                session_id=session_id,
            )

            logger.debug(f"[Agent {execution_id[:8]}] Chat result: ok={chat_result.get('ok')}, suggestions={len(chat_result.get('suggestions', []))}")

            if not chat_result.get("ok"):
                execution["error"] = chat_result.get("error", "Failed to get workflow from flyto-pro")
                execution["state"] = "failed"
                execution["ok"] = False
                break

            # Extract workflow from suggestions
            suggestions = chat_result.get("suggestions", [])
            workflow_yaml = None

            if suggestions:
                # Get the first (best) suggestion
                best_suggestion = suggestions[0]
                workflow_yaml = best_suggestion.get("yaml_content")
                execution["last_decision"] = "execute_workflow"
                execution["last_reason"] = f"Using suggestion: {best_suggestion.get('name', 'workflow')}"
                logger.info(f"Agent {execution_id}: Found workflow suggestion with {len(suggestions)} options")
            else:
                # No suggestions - check if message indicates completion or failure
                ai_message = chat_result.get("message") or ""
                if ai_message and any(word in ai_message.lower() for word in ["complete", "done", "finished", "success"]):
                    execution["state"] = "completed"
                    execution["ok"] = True
                    execution["final_output"] = {"message": ai_message}
                    break
                else:
                    execution["last_decision"] = "give_up"
                    execution["last_reason"] = "No workflow suggestions available"
                    execution["state"] = "failed"
                    execution["ok"] = False
                    execution["error"] = "No workflow suggestions from flyto-pro"
                    break

            if not workflow_yaml:
                execution["error"] = "No workflow YAML in suggestion"
                execution["state"] = "failed"
                execution["ok"] = False
                break

            # =========================================
            # ACT: Execute workflow locally
            # =========================================
            execution["state"] = "acting"
            logger.info(f"Agent {execution_id}: Executing workflow locally")
            logger.debug(f"Agent {execution_id}: Workflow YAML:\n{workflow_yaml[:500]}")

            exec_result = await _execute_workflow_locally(
                workflow_yaml=workflow_yaml,
                variables=request.context or {},
            )

            execution["last_result"] = exec_result
            logger.debug(f"[Agent {execution_id}] Execution result: ok={exec_result.get('ok')}, status={exec_result.get('status')}, error={exec_result.get('error')}")

            # Handle rate limiting - short pause then retry
            error_msg = exec_result.get("error") or ""
            if error_msg and ("rate limit" in error_msg.lower() or "concurrent" in error_msg.lower()):
                logger.warning(f"Agent {execution_id}: Rate limited, waiting 2s before retry...")
                await asyncio.sleep(2)
                # Don't count this as a real iteration
                execution["iteration"] = iteration - 1
                continue

            # =========================================
            # CHECK: Validate result
            # =========================================
            execution["state"] = "checking"

            if exec_result.get("ok"):
                # Workflow executed successfully
                result_data = exec_result.get("result", {})
                execution["state"] = "completed"
                execution["ok"] = True
                execution["final_output"] = result_data
                logger.info(f"Agent {execution_id}: Goal achieved with result: {result_data}")
                break
            else:
                # Execution failed - try again with error context
                error = exec_result.get("error", "Unknown error")
                logger.warning(f"Agent {execution_id}: Iteration {iteration} failed: {error}")

                # Track consecutive failures with same error
                last_error = execution.get("_last_error", "")
                if error == last_error:
                    execution["_error_repeat_count"] = execution.get("_error_repeat_count", 0) + 1
                else:
                    execution["_last_error"] = error
                    execution["_error_repeat_count"] = 1

                # Give up if same error repeats 3 times
                if execution.get("_error_repeat_count", 0) >= 3:
                    logger.error(f"Agent {execution_id}: Same error repeated 3 times, giving up")
                    execution["state"] = "failed"
                    execution["ok"] = False
                    execution["error"] = f"Repeated failure: {error}"
                    break

            # Continue to next iteration
            await asyncio.sleep(0.5)

        else:
            # Max iterations reached
            execution["state"] = "failed"
            execution["ok"] = False
            execution["error"] = f"Max iterations ({request.max_iterations}) reached"

    except Exception as e:
        logger.error(f"Agent execution error: {e}", exc_info=True)
        execution["state"] = "failed"
        execution["error"] = str(e)
        execution["ok"] = False

    finally:
        execution["completed_at"] = datetime.now().isoformat()


async def _run_mock_agent(execution_id: str, request: AgentExecuteRequest, execution: Dict):
    """
    Mock agent simulation for UI development.
    Simulates the Observe -> Think -> Act -> Check loop.
    """
    states = ["observing", "thinking", "acting", "checking"]

    for iteration in range(1, min(request.max_iterations + 1, 6)):
        execution["iteration"] = iteration

        for state in states:
            execution["state"] = state
            await asyncio.sleep(0.5)  # Simulate processing time

            # Simulate state-specific data
            if state == "thinking":
                execution["last_decision"] = "execute_workflow" if iteration < 5 else "complete"
                execution["last_reason"] = f"Analyzing step {iteration} results..."

        execution["llm_calls"] = iteration * 2

        # Complete after a few iterations for demo
        if iteration >= 5:
            break

    # Mark as completed
    execution["state"] = "completed"
    execution["ok"] = True
    execution["final_output"] = {
        "message": f"Mock agent completed goal: {request.goal[:50]}...",
        "iterations": execution["iteration"],
        "tools_used": request.tools_allowed[:2],
    }


# ============================================
# API Endpoints (specific paths MUST come before /{execution_id})
# ============================================


@router.get("/health")
async def agent_health():
    """Health check endpoint for agent API."""
    return {
        "ok": True,
        "status": "healthy",
        "service": "agent",
        "version": "1.0.0",
    }


@router.get("/tools", response_model=ToolsResponse)
async def list_available_tools():
    """
    List available tools/modules that agents can use.
    """
    tools = []

    try:
        from core.modules.registry import ModuleRegistry
        registry = ModuleRegistry()
        registered_modules = registry.get_all_modules()
        for module_id, module_class in registered_modules.items():
            category = module_id.split(".")[0] if "." in module_id else "other"
            tools.append(ToolInfo(
                id=module_id,
                name=getattr(module_class, "module_name", module_id),
                description=getattr(module_class, "module_description", ""),
                category=category,
            ))
    except (AttributeError, ImportError, RuntimeError):
        mock_tools = [
            ("browser.click", "Click Element", "Click on a web element", "browser"),
            ("browser.type", "Type Text", "Type text into input field", "browser"),
            ("browser.screenshot", "Screenshot", "Take page screenshot", "browser"),
            ("file.read", "Read File", "Read file contents", "file"),
            ("file.write", "Write File", "Write to file", "file"),
            ("http.get", "HTTP GET", "Make GET request", "http"),
            ("http.post", "HTTP POST", "Make POST request", "http"),
            ("code.javascript", "Run JS", "Execute JavaScript", "code"),
            ("code.python", "Run Python", "Execute Python code", "code"),
            ("ai.llm", "LLM Query", "Query language model", "ai"),
        ]

        for tool_id, name, desc, cat in mock_tools:
            tools.append(ToolInfo(
                id=tool_id,
                name=name,
                description=desc,
                category=cat,
            ))

    return ToolsResponse(
        ok=True,
        tools=tools,
        categories=TOOL_CATEGORIES,
    )


@router.get("/")
async def agent_info():
    """
    Get agent API information.
    """
    return {
        "ok": True,
        "name": "AI Agent API",
        "version": "1.0.0",
        "description": "Autonomous AI agent execution with Observe-Think-Act-Check loop",
        "endpoints": [
            "POST /agent/execute - Start agent execution",
            "GET /agent/{id} - Get execution status",
            "POST /agent/{id}/stop - Stop execution",
            "GET /agent/{id}/stream - Stream status updates (SSE)",
            "GET /agent/tools - List available tools",
            "GET /agent/health - Health check",
        ],
        "states": [
            "initializing", "observing", "thinking", "acting", "checking",
            "waiting_tool", "waiting_input",
            "completed", "failed", "paused"
        ],
    }


@router.post("/execute", response_model=AgentExecuteResponse)
async def execute_agent(
    request: AgentExecuteRequest,
    background_tasks: BackgroundTasks
):
    """
    Start an AI agent execution.

    The agent will run in the background, iterating through:
    1. OBSERVE - Collect current state
    2. THINK - Analyze and decide next action
    3. ACT - Execute the decision
    4. CHECK - Validate if goal is achieved

    Use GET /agent/{execution_id} to check status.
    """
    execution_id = str(uuid.uuid4())

    # Initialize execution record
    _executions[execution_id] = {
        "id": execution_id,
        "goal": request.goal,
        "provider": request.provider,
        "model": request.model,
        "state": "pending",
        "iteration": 0,
        "max_iterations": request.max_iterations,
        "llm_calls": 0,
        "ok": False,
        "started_at": None,
        "completed_at": None,
        "error": None,
        "final_output": None,
        "last_decision": None,
        "last_reason": None,
    }

    # Start agent in background
    background_tasks.add_task(_run_agent, execution_id, request)

    return AgentExecuteResponse(
        ok=True,
        execution_id=execution_id,
        message="Agent execution started"
    )


@router.get("/{execution_id}", response_model=AgentStatusResponse)
async def get_agent_status(execution_id: str):
    """
    Get the current status of an agent execution.
    """
    execution = _get_execution(execution_id)

    return AgentStatusResponse(
        ok=execution.get("ok", False),
        execution_id=execution_id,
        state=execution.get("state", "unknown"),
        iteration=execution.get("iteration", 0),
        max_iterations=execution.get("max_iterations", 0),
        llm_calls=execution.get("llm_calls", 0),
        started_at=execution.get("started_at"),
        completed_at=execution.get("completed_at"),
        error=execution.get("error"),
        final_output=execution.get("final_output"),
    )


@router.post("/{execution_id}/stop")
async def stop_agent(execution_id: str):
    """
    Stop a running agent execution.
    """
    execution = _get_execution(execution_id)

    if execution.get("state") in ["completed", "failed", "paused"]:
        return {"ok": False, "message": f"Agent is already {execution['state']}"}

    # Mark as stopped
    execution["state"] = "paused"
    execution["error"] = "Stopped by user"
    execution["completed_at"] = datetime.now().isoformat()

    return {"ok": True, "message": "Agent stopped"}


@router.get("/{execution_id}/stream")
async def stream_agent_status(execution_id: str):
    """
    Stream agent status updates via Server-Sent Events (SSE).

    Returns real-time state changes as the agent executes.
    """
    execution = _get_execution(execution_id)

    async def event_generator():
        last_state = None
        last_iteration = -1

        while True:
            current_state = execution.get("state")
            current_iteration = execution.get("iteration", 0)

            # Send update if state or iteration changed
            if current_state != last_state or current_iteration != last_iteration:
                data = {
                    "state": current_state,
                    "iteration": current_iteration,
                    "max_iterations": execution.get("max_iterations", 0),
                    "llm_calls": execution.get("llm_calls", 0),
                    "last_decision": execution.get("last_decision"),
                    "last_reason": execution.get("last_reason"),
                }
                yield f"data: {data}\n\n"
                last_state = current_state
                last_iteration = current_iteration

            # Stop if execution completed
            if current_state in ["completed", "failed", "paused"]:
                final_data = {
                    "state": current_state,
                    "ok": execution.get("ok", False),
                    "final_output": execution.get("final_output"),
                    "error": execution.get("error"),
                }
                yield f"data: {final_data}\n\n"
                break

            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
