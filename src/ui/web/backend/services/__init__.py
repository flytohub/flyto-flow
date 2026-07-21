"""
Flyto2 Backend Services

Core services for workflow execution and module management.

Imports are lazy to avoid pulling in heavy dependencies (flyto-core)
when only lightweight services are needed (e.g., main_web.py).
"""


def __getattr__(name):
    if name in ("get_execution_manager", "ExecutionManager"):
        from services.runtime.execution_manager import get_execution_manager, ExecutionManager
        return get_execution_manager if name == "get_execution_manager" else ExecutionManager
    if name == "ModuleScanner":
        from services.infra.module_scanner import ModuleScanner
        return ModuleScanner
    if name == "get_log_manager":
        from services.observability.log_manager import get_log_manager
        return get_log_manager
    raise AttributeError(f"module 'services' has no attribute {name!r}")


__all__ = [
    'get_execution_manager',
    'ExecutionManager',
    'ModuleScanner',
    'get_log_manager',
]
