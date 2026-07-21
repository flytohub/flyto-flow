"""
Debug Package

Provides debugging capabilities for workflow executions:
- Record & Replay: View historical executions and replay them
- Execution Timeline: Visualize execution flow
- Rerun strategies: Rehydrate vs Recompute modes
"""

from services.debug.models import (
    TimelineEvent,
    ExecutionTimeline,
    RerunMode,
    RerunConfig,
    RerunResult,
)
from services.debug.timeline import (
    get_timeline,
    get_node_detail,
    get_variables_at_step,
)
from services.debug.rerun import (
    replay_execution,
    rerun_from_node,
)
from services.debug.comparison import compare_executions
from services.debug.error_analysis import (
    get_error_analysis,
    get_fix_suggestions,
)

# DebugService class for backwards compatibility
from services.debug.service import DebugService

__all__ = [
    # Models
    "TimelineEvent",
    "ExecutionTimeline",
    "RerunMode",
    "RerunConfig",
    "RerunResult",
    # Timeline
    "get_timeline",
    "get_node_detail",
    "get_variables_at_step",
    # Rerun
    "replay_execution",
    "rerun_from_node",
    # Comparison
    "compare_executions",
    # Error Analysis
    "get_error_analysis",
    "get_fix_suggestions",
    # Service
    "DebugService",
]
