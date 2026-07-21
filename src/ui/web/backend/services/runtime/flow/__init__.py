"""
Flow Control Nodes Package

Advanced flow control for workflow execution:
- Sub-workflow invocation
- Enhanced loops (ForEach, While)
- Parallel execution (Fork/Join)
- Condition evaluation
- Try-Catch-Finally blocks
- Compensation/Saga patterns
"""

from services.runtime.flow.subworkflow import (
    SubworkflowMode,
    SubworkflowConfig,
    SubworkflowResult,
    SubworkflowExecutor,
)

from services.runtime.flow.loop import (
    LoopBreakException,
    LoopContinueException,
    ForEachConfig,
    WhileConfig,
    LoopResult,
    LoopExecutor,
)

from services.runtime.flow.fork_join import (
    JoinStrategy,
    Branch,
    ForkJoinConfig,
    BranchResult,
    ForkJoinResult,
    ForkJoinExecutor,
)

from services.runtime.flow.condition import ConditionEvaluator

from services.runtime.flow.models import (
    OnErrorStrategy,
    ErrorHandlerConfig,
    TryCatchFinallyConfig,
    TryCatchFinallyResult,
    CompensationOrder,
    OnCompensationFailure,
    CompensationConfig,
    SagaStep,
    SagaConfig,
    CompensationResult,
    SagaResult,
)

from services.runtime.flow.try_catch import TryCatchFinallyExecutor
from services.runtime.flow.saga import SagaExecutor
from services.runtime.flow.helpers import create_try_catch_finally, create_saga_step

__all__ = [
    # Sub-workflow
    'SubworkflowMode',
    'SubworkflowConfig',
    'SubworkflowResult',
    'SubworkflowExecutor',
    # Loop
    'LoopBreakException',
    'LoopContinueException',
    'ForEachConfig',
    'WhileConfig',
    'LoopResult',
    'LoopExecutor',
    # Fork/Join
    'JoinStrategy',
    'Branch',
    'ForkJoinConfig',
    'BranchResult',
    'ForkJoinResult',
    'ForkJoinExecutor',
    # Condition
    'ConditionEvaluator',
    # Error Handling Models
    'OnErrorStrategy',
    'ErrorHandlerConfig',
    'TryCatchFinallyConfig',
    'TryCatchFinallyResult',
    'CompensationOrder',
    'OnCompensationFailure',
    'CompensationConfig',
    'SagaStep',
    'SagaConfig',
    'CompensationResult',
    'SagaResult',
    # Executors
    'TryCatchFinallyExecutor',
    'SagaExecutor',
    # Helpers
    'create_try_catch_finally',
    'create_saga_step',
]
