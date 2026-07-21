"""
Flow Control Helpers

Helper functions for creating flow control configurations.
"""

from typing import Any, Dict, List, Optional

from services.error_taxonomy import ErrorCategory
from services.runtime.flow.models import (
    CompensationConfig,
    SagaStep,
    TryCatchFinallyConfig,
)


def create_try_catch_finally(
    try_steps: List[str],
    catch_steps: Optional[List[str]] = None,
    finally_steps: Optional[List[str]] = None,
    catch_errors: Optional[List[str]] = None,
) -> TryCatchFinallyConfig:
    """
    Create a Try-Catch-Finally configuration.

    Args:
        try_steps: Steps in try block
        catch_steps: Steps in catch block
        finally_steps: Steps in finally block
        catch_errors: Error categories to catch

    Returns:
        TryCatchFinallyConfig
    """
    errors = []
    if catch_errors:
        errors = [ErrorCategory(e) for e in catch_errors]

    return TryCatchFinallyConfig(
        try_steps=try_steps,
        catch_steps=catch_steps or [],
        finally_steps=finally_steps or [],
        catch_errors=errors,
    )


def create_saga_step(
    step_id: str,
    module_id: str,
    params: Optional[Dict[str, Any]] = None,
    compensation_module: Optional[str] = None,
    compensation_params: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
) -> SagaStep:
    """
    Create a Saga step with optional compensation.

    Args:
        step_id: Step identifier
        module_id: Module to execute
        params: Module parameters
        compensation_module: Compensation module ID
        compensation_params: Compensation parameters
        idempotency_key: Idempotency key for compensation

    Returns:
        SagaStep
    """
    compensation = None
    if compensation_module:
        compensation = CompensationConfig(
            module_id=compensation_module,
            params=compensation_params or {},
            idempotency_key=idempotency_key,
        )

    return SagaStep(
        step_id=step_id,
        module_id=module_id,
        params=params or {},
        compensation=compensation,
    )
