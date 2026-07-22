"""
LLM Context Packaging Service

Provides context compilation and session persistence for LLM sessions.
Implements the Context Packaging system from CONTEXT_PACKAGING.md

Usage:
    from services.llm_context import (
        ContextCompiler,
        TaskType,
        get_session_storage,
        get_context_updater,
    )

    # Compile context for a task
    compiler = ContextCompiler(project_root="/path/to/project")
    context = compiler.compile(TaskType.BUGFIX)
    prompt = context.to_prompt()

    # Save/load sessions
    storage = get_session_storage()
    storage.save_session("session_123", session_data)
    session = storage.load_session("session_123")

    # Update context files
    updater = get_context_updater()
    updater.append_event("done", "Updated the workflow")
    updater.update_status(done_task="T-201")
"""

from .compiler import (
    ContextCompiler,
    ContextPackage,
    TaskType,
    compile_context_for_task,
    TASK_CONTEXT_RULES,
)

from .storage import (
    SessionStorage,
    ContextUpdater,
    get_session_storage,
    get_context_updater,
)

__all__ = [
    # Compiler
    "ContextCompiler",
    "ContextPackage",
    "TaskType",
    "compile_context_for_task",
    "TASK_CONTEXT_RULES",
    # Storage
    "SessionStorage",
    "ContextUpdater",
    "get_session_storage",
    "get_context_updater",
]
