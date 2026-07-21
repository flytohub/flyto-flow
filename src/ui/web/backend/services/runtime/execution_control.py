"""
Execution Control Service

Provides pause/resume/step control for running executions.
Implements the control plane for interactive debugging.

Design:
- Decoupled from execution engine
- Uses event-based communication
- Supports both sync and async pause points
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ControlCommand(str, Enum):
    """Commands that can be sent to a running execution."""
    PAUSE = "pause"
    RESUME = "resume"
    STEP_OVER = "step_over"
    STEP_INTO = "step_into"
    CANCEL = "cancel"


class PauseReason(str, Enum):
    """Reasons for execution pause."""
    USER_REQUEST = "user_request"
    BREAKPOINT = "breakpoint"
    ERROR_PAUSE = "error_pause"
    STEP_MODE = "step_mode"
    TRIAL_BATCH_COMPLETE = "trial_batch_complete"


@dataclass
class ExecutionState:
    """Current state of a paused execution."""
    execution_id: str
    status: str
    current_node_id: Optional[str] = None
    current_step_index: int = 0
    total_steps: int = 0
    paused_at: Optional[str] = None
    pause_reason: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    can_resume: bool = True
    can_step: bool = True
    error_message: Optional[str] = None


@dataclass
class ControlEvent:
    """Event sent to execution controller."""
    command: ControlCommand
    execution_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)


class ExecutionController:
    """
    Controls execution flow for pause/resume/step operations.

    Each running execution can register a control channel.
    Commands are sent through the channel to control execution.
    """

    def __init__(self):
        """Initialize control signals, states, and breakpoint tracking."""
        # Map of execution_id -> asyncio.Event for pause signals
        self._pause_signals: Dict[str, asyncio.Event] = {}
        # Map of execution_id -> asyncio.Event for resume signals
        self._resume_signals: Dict[str, asyncio.Event] = {}
        # Map of execution_id -> current state
        self._states: Dict[str, ExecutionState] = {}
        # Map of execution_id -> set of breakpoint node_ids
        self._breakpoints: Dict[str, Set[str]] = {}
        # Map of execution_id -> step mode flag
        self._step_mode: Dict[str, bool] = {}
        # Map of execution_id -> last executed node_id (for post-execution breakpoints)
        self._last_executed: Dict[str, Optional[str]] = {}
        # Map of execution_id -> ignore breakpoints flag (for "run to end")
        self._ignore_breakpoints: Dict[str, bool] = {}
        # Callbacks for state changes
        self._state_callbacks: List[Callable[[str, ExecutionState], None]] = []

    def register_execution(self, execution_id: str) -> None:
        """Register an execution for control."""
        self._pause_signals[execution_id] = asyncio.Event()
        self._resume_signals[execution_id] = asyncio.Event()
        self._resume_signals[execution_id].set()  # Initially not paused
        self._states[execution_id] = ExecutionState(
            execution_id=execution_id,
            status="running"
        )
        self._breakpoints[execution_id] = set()
        self._step_mode[execution_id] = False
        self._last_executed[execution_id] = None
        self._ignore_breakpoints[execution_id] = False
        logger.debug(f"Registered execution for control: {execution_id}")

    def unregister_execution(self, execution_id: str) -> None:
        """Unregister an execution."""
        self._pause_signals.pop(execution_id, None)
        self._resume_signals.pop(execution_id, None)
        self._states.pop(execution_id, None)
        self._breakpoints.pop(execution_id, None)
        self._step_mode.pop(execution_id, None)
        self._last_executed.pop(execution_id, None)
        self._ignore_breakpoints.pop(execution_id, None)
        logger.debug(f"Unregistered execution: {execution_id}")

    def is_registered(self, execution_id: str) -> bool:
        """Check if execution is registered for control."""
        return execution_id in self._pause_signals

    async def request_pause(
        self,
        execution_id: str,
        reason: PauseReason = PauseReason.USER_REQUEST
    ) -> bool:
        """
        Request an execution to pause.

        Returns True if pause signal was sent successfully.
        The execution will pause at the next safe point.
        """
        if execution_id not in self._pause_signals:
            logger.warning(f"Execution not registered: {execution_id}")
            return False

        self._pause_signals[execution_id].set()
        self._resume_signals[execution_id].clear()

        state = self._states.get(execution_id)
        if state:
            state.status = "pausing"
            state.pause_reason = reason.value

        logger.info(f"Pause requested for execution: {execution_id}, reason: {reason}")
        return True

    async def request_resume(self, execution_id: str) -> bool:
        """
        Request a paused execution to resume.

        Returns True if resume signal was sent successfully.
        """
        if execution_id not in self._resume_signals:
            logger.warning(f"Execution not registered: {execution_id}")
            return False

        state = self._states.get(execution_id)
        # Allow resume if status is paused or pausing (transition state)
        if state and state.status not in ("paused", "pausing"):
            logger.warning(f"Execution not paused: {execution_id}, status: {state.status}")
            return False

        self._step_mode[execution_id] = False
        self._pause_signals[execution_id].clear()
        self._resume_signals[execution_id].set()

        if state:
            state.status = "running"
            state.pause_reason = None

            # Notify callbacks about resume
            for callback in self._state_callbacks:
                try:
                    callback(execution_id, state)
                except Exception as e:
                    logger.error(f"State callback error on resume: {e}")

        logger.info(f"Resume requested for execution: {execution_id}")
        return True

    async def request_step(self, execution_id: str) -> bool:
        """
        Request a single step execution (step over).

        Returns True if step signal was sent successfully.
        """
        if execution_id not in self._resume_signals:
            return False

        state = self._states.get(execution_id)
        if state and state.status != "paused":
            return False

        # Enable step mode - will pause after next node
        self._step_mode[execution_id] = True
        self._pause_signals[execution_id].clear()
        self._resume_signals[execution_id].set()

        if state:
            state.status = "stepping"

        logger.info(f"Step requested for execution: {execution_id}")
        return True

    async def check_pause_point(
        self,
        execution_id: str,
        step_index: int,
        step_id: str,
        variables: Dict[str, Any],
        node_outputs: Dict[str, Any],
        internal_should_pause: bool = False
    ) -> bool:
        """
        Check if execution should pause at current point.

        Called by WorkflowEngine before each step execution.
        Returns True if execution was paused and has now resumed.

        Args:
            execution_id: The execution ID
            step_index: Current step index
            step_id: Current step ID (about to execute)
            variables: Current variable state
            node_outputs: Outputs from completed nodes
            internal_should_pause: Ignored - we handle breakpoints ourselves
        """
        # Auto-register if not registered (for late registration support)
        if execution_id not in self._pause_signals:
            self.register_execution(execution_id)

        should_pause = False
        reason = None

        # Get the previous node (which just finished executing)
        prev_node = self._last_executed.get(execution_id)

        # Update to current node (which is about to execute)
        self._last_executed[execution_id] = step_id

        # Check for external pause request (from API)
        if self._pause_signals[execution_id].is_set():
            should_pause = True
            reason = PauseReason.USER_REQUEST

        # Check for breakpoint on PREVIOUS node (post-execution breakpoint)
        # This means: pause AFTER the breakpoint node has executed, BEFORE the next node starts
        elif not self._ignore_breakpoints.get(execution_id, False):
            breakpoints = self._breakpoints.get(execution_id, set())
            if prev_node and prev_node in breakpoints:
                should_pause = True
                reason = PauseReason.BREAKPOINT
                logger.info(f"Breakpoint hit: node {prev_node} completed, pausing before {step_id}")

        # Check for step mode (step-by-step execution)
        if not should_pause and self._step_mode.get(execution_id, False):
            should_pause = True
            reason = PauseReason.STEP_MODE
            self._step_mode[execution_id] = False

        # Note: We ignore internal_should_pause - we handle breakpoints ourselves

        if should_pause:
            await self._do_pause(
                execution_id, step_id, step_index,
                variables, node_outputs, reason
            )
            return True

        return False

    async def _do_pause(
        self,
        execution_id: str,
        step_id: str,
        step_index: int,
        variables: Dict[str, Any],
        node_outputs: Dict[str, Any],
        reason: PauseReason
    ) -> None:
        """Execute the pause and wait for resume."""
        state = self._states.get(execution_id)
        if state:
            state.status = "paused"
            state.current_node_id = step_id
            state.current_step_index = step_index
            state.paused_at = datetime.now(timezone.utc).isoformat()
            state.pause_reason = reason.value
            state.variables = variables.copy()
            state.node_outputs = node_outputs.copy()

        logger.info(f"Execution paused: {execution_id} at step {step_id}")

        # Notify callbacks
        for callback in self._state_callbacks:
            try:
                callback(execution_id, state)
            except Exception as e:
                logger.error(f"State callback error: {e}")

        # Wait for resume signal
        self._resume_signals[execution_id].clear()
        await self._resume_signals[execution_id].wait()

        logger.info(f"Execution resumed: {execution_id}")

    def get_state(self, execution_id: str) -> Optional[ExecutionState]:
        """Get current state of an execution."""
        return self._states.get(execution_id)

    def set_breakpoint(self, execution_id: str, node_id: str) -> bool:
        """Set a breakpoint at a node."""
        if execution_id not in self._breakpoints:
            self._breakpoints[execution_id] = set()
        self._breakpoints[execution_id].add(node_id)
        logger.debug(f"Breakpoint set: {execution_id} at {node_id}")
        return True

    def remove_breakpoint(self, execution_id: str, node_id: str) -> bool:
        """Remove a breakpoint from a node."""
        if execution_id in self._breakpoints:
            self._breakpoints[execution_id].discard(node_id)
            return True
        return False

    def list_breakpoints(self, execution_id: str) -> List[str]:
        """List all breakpoints for an execution."""
        return list(self._breakpoints.get(execution_id, set()))

    async def run_to_end(self, execution_id: str) -> bool:
        """
        Resume execution and ignore all breakpoints (run to completion).
        Returns True if successful.
        """
        if execution_id not in self._resume_signals:
            logger.warning(f"Execution not registered: {execution_id}")
            return False

        state = self._states.get(execution_id)
        if state and state.status not in ("paused", "pausing"):
            logger.warning(f"Execution not paused: {execution_id}, status: {state.status}")
            return False

        # Set flag to ignore breakpoints
        self._ignore_breakpoints[execution_id] = True
        self._step_mode[execution_id] = False
        self._pause_signals[execution_id].clear()
        self._resume_signals[execution_id].set()

        if state:
            state.status = "running"
            state.pause_reason = None

        logger.info(f"Run to end requested for execution: {execution_id}")
        return True

    def add_state_callback(
        self,
        callback: Callable[[str, ExecutionState], None]
    ) -> None:
        """Add a callback for state changes."""
        self._state_callbacks.append(callback)

    def update_state(
        self,
        execution_id: str,
        node_id: Optional[str] = None,
        step_index: Optional[int] = None,
        total_steps: Optional[int] = None,
        variables: Optional[Dict[str, Any]] = None,
        node_outputs: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update execution state (called by worker during execution)."""
        state = self._states.get(execution_id)
        if not state:
            return

        if node_id is not None:
            state.current_node_id = node_id
        if step_index is not None:
            state.current_step_index = step_index
        if total_steps is not None:
            state.total_steps = total_steps
        if variables is not None:
            state.variables = variables
        if node_outputs is not None:
            state.node_outputs = node_outputs


# Global singleton instance
_controller: Optional[ExecutionController] = None


def get_controller() -> ExecutionController:
    """Get the global execution controller instance."""
    global _controller
    if _controller is None:
        _controller = ExecutionController()
    return _controller


# Alias for compatibility
get_execution_controller = get_controller
