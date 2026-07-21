#!/usr/bin/env python3
"""
Template Worker Subprocess

Executes templates in an isolated subprocess with restricted permissions.
Communicates via JSON-RPC over stdin/stdout.

This worker is spawned by TemplateRuntime and executes templates using
a restricted subset of flyto-core modules.
"""

import asyncio
import json
import logging
import os
import sys
import fnmatch
from typing import Any, Dict, List, Optional, Set

# Configure logging to stderr (stdout is for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Protocol constants
JSONRPC_VERSION = "2.0"
WORKER_VERSION = "1.0.0"


class ModuleRegistry:
    """
    Restricted module registry for template execution.

    Only loads modules that are in the allowed list and not in the disallowed list.
    """

    def __init__(
        self,
        allowed_patterns: List[str],
        disallowed_patterns: List[str],
    ):
        """Initialize with allowed and disallowed module patterns."""
        self.allowed_patterns = allowed_patterns
        self.disallowed_patterns = disallowed_patterns
        self._modules: Dict[str, Any] = {}
        self._loaded = False

    def is_module_allowed(self, module_id: str) -> bool:
        """Check if a module is allowed."""
        # Check disallowed first
        for pattern in self.disallowed_patterns:
            if fnmatch.fnmatch(module_id, pattern):
                return False

        # Check allowed
        for pattern in self.allowed_patterns:
            if fnmatch.fnmatch(module_id, pattern):
                return True

        return False

    def load_modules(self):
        """Load allowed modules from flyto-core."""
        if self._loaded:
            return

        try:
            from core.modules import get_module_registry

            core_registry = get_module_registry()
            if core_registry:
                all_metadata = core_registry.get_all_metadata()
                for module_id in all_metadata.keys():
                    if self.is_module_allowed(module_id):
                        self._modules[module_id] = module_id
                        logger.debug(f"Loaded module: {module_id}")

            logger.info(f"Loaded {len(self._modules)} allowed modules")
            self._loaded = True

        except ImportError as e:
            logger.error(f"Failed to import flyto-core: {e}")
        except Exception as e:
            logger.error(f"Failed to load modules: {e}")

    def module_count(self) -> int:
        """Get number of loaded allowed modules."""
        return len(self._modules)

    def get_module(self, module_id: str) -> Optional[str]:
        """Get a module by ID if allowed."""
        if not self._loaded:
            self.load_modules()

        if not self.is_module_allowed(module_id):
            return None

        return self._modules.get(module_id)


class TemplateExecutor:
    """
    Executes templates using flyto-core workflow engine.

    Operates in a restricted environment with limited module access.
    """

    def __init__(self, registry: ModuleRegistry):
        """Initialize with a restricted module registry."""
        self.registry = registry
        self._workflow_engine = None

    def _normalize_template_module(self, module_id: str, params: Dict[str, Any]) -> tuple:
        """
        Normalize template module IDs.

        Converts:
        - template.invoke:xxx -> template.invoke (with template_id in params)
        - template.xxx -> template.invoke (with template_id in params)

        Returns:
            Tuple of (normalized_module_id, updated_params)
        """
        if not module_id:
            return module_id, params

        new_params = dict(params) if params else {}

        if module_id.startswith('template.invoke:'):
            template_id = module_id.replace('template.invoke:', '')
            new_params['template_id'] = template_id
            new_params['library_id'] = template_id
            return 'template.invoke', new_params

        if module_id.startswith('template.') and module_id != 'template.invoke':
            template_id = module_id.replace('template.', '')
            new_params['template_id'] = template_id
            new_params['library_id'] = template_id
            return 'template.invoke', new_params

        return module_id, params

    def _get_workflow_engine(self):
        """Get or create workflow engine."""
        if self._workflow_engine is None:
            try:
                from core.engine.workflow import WorkflowEngine
                self._workflow_engine = WorkflowEngine()
            except ImportError:
                logger.warning("WorkflowEngine not available, using simple executor")
        return self._workflow_engine

    async def execute(
        self,
        template_id: str,
        definition: Dict[str, Any],
        input_params: Dict[str, Any],
        execution_id: str,
        config: Dict[str, Any],
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute a template.

        Args:
            template_id: Template ID
            definition: Template definition with steps
            input_params: Input parameters
            execution_id: Execution ID for tracking
            config: Execution config
            progress_callback: Callback for step progress

        Returns:
            Execution result
        """
        steps = definition.get("steps", [])
        if not steps:
            return {
                "ok": True,
                "data": input_params,
            }

        # Validate all steps use allowed modules
        for i, step in enumerate(steps):
            raw_module_id = step.get("module") or step.get("moduleId")
            if not raw_module_id:
                return {
                    "ok": False,
                    "error": f"Step {i} has no module specified",
                    "error_code": "VALIDATION_ERROR",
                }

            # Normalize template module IDs for validation
            module_id, _ = self._normalize_template_module(raw_module_id, {})

            if not self.registry.is_module_allowed(module_id):
                return {
                    "ok": False,
                    "error": f"Module '{module_id}' is not allowed in templates",
                    "error_code": "MODULE_NOT_ALLOWED",
                }

        # Execute steps sequentially
        current_data = input_params
        total_steps = len(steps)

        for i, step in enumerate(steps):
            step_id = step.get("id") or f"step_{i}"
            raw_module_id = step.get("module") or step.get("moduleId")
            step_params = step.get("params", {})

            # Normalize template module IDs
            module_id, step_params = self._normalize_template_module(raw_module_id, step_params)

            # Report progress
            if progress_callback:
                progress_callback({
                    "executionId": execution_id,
                    "stepId": step_id,
                    "stepIndex": i,
                    "totalSteps": total_steps,
                    "status": "running",
                    "moduleId": module_id,
                })

            try:
                # Resolve parameters with current data
                resolved_params = self._resolve_params(step_params, current_data, input_params)

                # Execute the step
                result = await self._execute_step(module_id, resolved_params)

                if not result.get("ok", False):
                    if progress_callback:
                        progress_callback({
                            "executionId": execution_id,
                            "stepId": step_id,
                            "stepIndex": i,
                            "totalSteps": total_steps,
                            "status": "failed",
                            "error": result.get("error"),
                        })
                    return result

                # Update current data with result
                current_data = result.get("data", result)

                if progress_callback:
                    progress_callback({
                        "executionId": execution_id,
                        "stepId": step_id,
                        "stepIndex": i,
                        "totalSteps": total_steps,
                        "status": "completed",
                    })

            except Exception as e:
                logger.error(f"Step {step_id} failed: {e}")
                if progress_callback:
                    progress_callback({
                        "executionId": execution_id,
                        "stepId": step_id,
                        "stepIndex": i,
                        "totalSteps": total_steps,
                        "status": "failed",
                        "error": str(e),
                    })
                return {
                    "ok": False,
                    "error": f"Step {step_id} failed: {str(e)}",
                    "error_code": "STEP_EXECUTION_FAILED",
                }

        return {
            "ok": True,
            "data": current_data,
        }

    def _resolve_params(
        self,
        params: Dict[str, Any],
        current_data: Dict[str, Any],
        input_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Resolve parameter placeholders.

        Supports:
        - ${input.key} - from input parameters
        - ${prev.key} - from previous step output
        - ${steps.stepId.key} - from specific step (not implemented yet)
        """
        resolved = {}

        for key, value in params.items():
            if isinstance(value, str):
                resolved[key] = self._resolve_string(value, current_data, input_params)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_params(value, current_data, input_params)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_string(v, current_data, input_params) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                resolved[key] = value

        return resolved

    def _resolve_string(
        self,
        value: str,
        current_data: Dict[str, Any],
        input_params: Dict[str, Any],
    ) -> Any:
        """Resolve a string that may contain placeholders."""
        # Direct reference
        if value.startswith("${") and value.endswith("}"):
            ref = value[2:-1]

            if ref.startswith("input."):
                key = ref[6:]
                return self._get_nested(input_params, key)
            elif ref.startswith("prev."):
                key = ref[5:]
                return self._get_nested(current_data, key)
            elif ref.startswith("prev"):
                # Just ${prev} means the whole previous output
                return current_data

        return value

    @staticmethod
    def _get_nested(data: Dict[str, Any], path: str) -> Any:
        """Get a nested value by dot-separated path."""
        from core.engine.variable_resolver import VariableResolver
        return VariableResolver.get_nested_value(data, path)

    async def _execute_step(self, module_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single module step."""
        try:
            # Use flyto-core runtime invoker
            from core.runtime import invoke

            result = await invoke(
                module_id=module_id,
                params=params,
            )
            return result

        except ImportError:
            # Fallback to direct module execution
            try:
                from core.modules import get_module_registry

                registry = get_module_registry()
                if not registry:
                    return {
                        "ok": False,
                        "error": "Module registry not available",
                    }

                module_class = registry.get(module_id)
                if not module_class:
                    return {
                        "ok": False,
                        "error": f"Module not found: {module_id}",
                    }

                module = module_class(params)
                module.validate_params()
                result = await module.execute()
                return result

            except Exception as e:
                return {
                    "ok": False,
                    "error": str(e),
                }


class WorkerServer:
    """
    JSON-RPC server for template worker.

    Reads requests from stdin, writes responses to stdout.
    """

    def __init__(self):
        """Initialize worker server from environment configuration."""
        allowed = os.environ.get("FLYTO_ALLOWED_MODULES", "").split(",")
        disallowed = os.environ.get("FLYTO_DISALLOWED_MODULES", "").split(",")

        self.registry = ModuleRegistry(
            allowed_patterns=[p.strip() for p in allowed if p.strip()],
            disallowed_patterns=[p.strip() for p in disallowed if p.strip()],
        )
        self.executor = TemplateExecutor(self.registry)
        self._running = False

    def send_response(self, request_id: int, result: Any = None, error: Any = None):
        """Send a JSON-RPC response to stdout."""
        response = {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
        }
        if error is not None:
            response["error"] = error
        else:
            response["result"] = result

        line = json.dumps(response) + "\n"
        sys.stdout.write(line)
        sys.stdout.flush()

    def send_notification(self, method: str, params: Dict[str, Any]):
        """Send a JSON-RPC notification to stdout."""
        notification = {
            "jsonrpc": JSONRPC_VERSION,
            "method": method,
            "params": params,
        }
        line = json.dumps(notification) + "\n"
        sys.stdout.write(line)
        sys.stdout.flush()

    async def handle_request(self, request: Dict[str, Any]):
        """Handle a JSON-RPC request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "handshake":
            await self.handle_handshake(request_id, params)
        elif method == "execute_template":
            await self.handle_execute_template(request_id, params)
        elif method == "ping":
            await self.handle_ping(request_id)
        elif method == "shutdown":
            await self.handle_shutdown(request_id, params)
        else:
            self.send_response(
                request_id,
                error={"code": -32601, "message": f"Method not found: {method}"},
            )

    async def handle_handshake(self, request_id: int, params: Dict[str, Any]):
        """Handle handshake request."""
        protocol_version = params.get("protocolVersion", "unknown")
        logger.info(f"Handshake received (protocol: {protocol_version})")

        # Load modules
        self.registry.load_modules()

        self.send_response(request_id, {
            "workerVersion": WORKER_VERSION,
            "protocolVersion": JSONRPC_VERSION,
            "modules_loaded": self.registry.module_count(),
        })

    async def handle_execute_template(self, request_id: int, params: Dict[str, Any]):
        """Handle execute_template request."""
        template_id = params.get("templateId")
        definition = params.get("definition", {})
        input_params = params.get("inputParams", {})
        execution_id = params.get("executionId", "unknown")
        config = params.get("config", {})

        logger.info(f"Executing template: {template_id} (execution: {execution_id})")

        def progress_callback(progress):
            self.send_notification("step_progress", progress)

        try:
            result = await self.executor.execute(
                template_id=template_id,
                definition=definition,
                input_params=input_params,
                execution_id=execution_id,
                config=config,
                progress_callback=progress_callback,
            )
            self.send_response(request_id, result)

        except Exception as e:
            logger.error(f"Template execution failed: {e}")
            self.send_response(
                request_id,
                error={"code": -32603, "message": str(e)},
            )

    async def handle_ping(self, request_id: int):
        """Handle ping request."""
        self.send_response(request_id, {"pong": True})

    async def handle_shutdown(self, request_id: int, params: Dict[str, Any]):
        """Handle shutdown request."""
        reason = params.get("reason", "unknown")
        logger.info(f"Shutdown requested: {reason}")

        self.send_response(request_id, {"acknowledged": True})
        self._running = False

    async def run(self):
        """Main loop - read from stdin and process requests."""
        self._running = True
        logger.info("Template worker started")

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        loop = asyncio.get_running_loop()
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while self._running:
            try:
                line = await reader.readline()
                if not line:
                    break

                data = line.decode("utf-8").strip()
                if not data:
                    continue

                try:
                    request = json.loads(data)
                    await self.handle_request(request)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    self.send_response(
                        0,
                        error={"code": -32700, "message": f"Parse error: {e}"},
                    )

            except Exception as e:
                logger.error(f"Error reading input: {e}")
                break

        logger.info("Template worker stopped")


async def main():
    """Entry point."""
    server = WorkerServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
