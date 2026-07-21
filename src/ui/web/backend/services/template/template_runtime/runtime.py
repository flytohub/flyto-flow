"""
Template Runtime Manager

Manages template execution in isolated subprocesses.
Non-official templates execute in restricted subprocesses for security.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from .protocol import (
    ProtocolEncoder,
    ProtocolDecoder,
    JsonRpcResponse,
    JsonRpcNotification,
    PROTOCOL_VERSION,
    ErrorCode,
)

logger = logging.getLogger(__name__)


class ProcessStatus(Enum):
    """Status of a template worker process."""
    STOPPED = "stopped"
    STARTING = "starting"
    READY = "ready"
    BUSY = "busy"
    UNHEALTHY = "unhealthy"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class TemplateProcessConfig:
    """Configuration for template worker process."""
    python_executable: str = "python3"
    env: Dict[str, str] = field(default_factory=dict)

    # Timeouts
    handshake_timeout_ms: int = 5000
    default_timeout_ms: int = 300000  # 5 minutes
    shutdown_timeout_ms: int = 5000

    # Resource limits
    max_memory_mb: int = 256
    max_cpu_percent: int = 50

    # Module restrictions
    allowed_modules: List[str] = field(default_factory=lambda: [
        "string.*",
        "array.*",
        "object.*",
        "math.*",
        "datetime.*",
        "json.*",
        "format.*",
        "convert.*",
        "logic.*",
        "flow.*",
        "compare.*",
        "validate.*",
    ])

    disallowed_modules: List[str] = field(default_factory=lambda: [
        "shell.*",
        "process.*",
        "filesystem.write",
        "filesystem.delete",
        "system.*",
    ])


@dataclass
class RestartPolicy:
    """Restart policy for crashed workers."""
    max_restarts: int = 3
    restart_window_seconds: int = 60
    backoff_seconds: List[int] = field(default_factory=lambda: [1, 2, 4])
    unhealthy_cooldown_seconds: int = 300


class TemplateProcess:
    """
    Manages a single template worker subprocess.

    Handles:
    - Process lifecycle (start, stop, restart)
    - JSON-RPC communication over stdio
    - Health checking
    - Crash detection and restart policy
    """

    def __init__(
        self,
        config: Optional[TemplateProcessConfig] = None,
        restart_policy: Optional[RestartPolicy] = None,
    ):
        """Initialize process with config and restart policy."""
        self.config = config or TemplateProcessConfig()
        self.restart_policy = restart_policy or RestartPolicy()

        self._process: Optional[asyncio.subprocess.Process] = None
        self._status = ProcessStatus.STOPPED
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}

        # Restart tracking
        self._restart_times: List[float] = []
        self._unhealthy_until: Optional[float] = None

        # Reader task
        self._reader_task: Optional[asyncio.Task] = None

        # Callbacks for notifications
        self._notification_handlers: Dict[str, Callable] = {}

    @property
    def status(self) -> ProcessStatus:
        """Get current process status."""
        return self._status

    @property
    def is_ready(self) -> bool:
        """Check if process is ready for invocations."""
        return self._status == ProcessStatus.READY

    @property
    def is_unhealthy(self) -> bool:
        """Check if process is marked unhealthy."""
        if self._status == ProcessStatus.UNHEALTHY:
            if self._unhealthy_until and time.time() >= self._unhealthy_until:
                self._status = ProcessStatus.STOPPED
                self._unhealthy_until = None
                self._restart_times.clear()
                return False
            return True
        return False

    def on_notification(self, method: str, handler: Callable):
        """Register a notification handler."""
        self._notification_handlers[method] = handler

    def _next_request_id(self) -> int:
        """Generate next request ID."""
        self._request_id += 1
        return self._request_id

    async def start(self) -> bool:
        """
        Start the template worker process.

        Returns:
            True if started successfully, False otherwise
        """
        if self.is_unhealthy:
            remaining = int(self._unhealthy_until - time.time()) if self._unhealthy_until else 0
            logger.warning(f"Template worker is unhealthy, cooldown: {remaining}s")
            return False

        if self._process is not None:
            logger.warning("Template worker already running")
            return True

        self._status = ProcessStatus.STARTING

        try:
            # Find worker script
            worker_path = Path(__file__).parent / "worker.py"
            if not worker_path.exists():
                logger.error(f"Worker script not found: {worker_path}")
                self._status = ProcessStatus.STOPPED
                return False

            cmd = [self.config.python_executable, str(worker_path)]

            # Build environment
            env = os.environ.copy()
            env.update(self.config.env)
            env["FLYTO_PROTOCOL_VERSION"] = PROTOCOL_VERSION
            env["FLYTO_MAX_MEMORY_MB"] = str(self.config.max_memory_mb)
            env["FLYTO_MAX_CPU_PERCENT"] = str(self.config.max_cpu_percent)
            env["FLYTO_ALLOWED_MODULES"] = ",".join(self.config.allowed_modules)
            env["FLYTO_DISALLOWED_MODULES"] = ",".join(self.config.disallowed_modules)

            logger.info("Starting template worker process")

            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            # Start reader task
            self._reader_task = asyncio.create_task(self._read_stdout())

            # Perform handshake
            success = await self._handshake()
            if success:
                self._status = ProcessStatus.READY
                logger.info("Template worker ready")
                return True
            else:
                await self.stop()
                return False

        except Exception as e:
            logger.error(f"Failed to start template worker: {e}")
            self._status = ProcessStatus.STOPPED
            return False

    async def stop(self, reason: str = "shutdown", grace_period_ms: int = 5000):
        """
        Stop the template worker process gracefully.

        Args:
            reason: Reason for shutdown
            grace_period_ms: Grace period before force kill
        """
        if self._process is None:
            return

        self._status = ProcessStatus.SHUTTING_DOWN

        try:
            # Send shutdown command
            request_id = self._next_request_id()
            msg = ProtocolEncoder.encode_shutdown(reason, grace_period_ms, request_id)
            await self._send(msg)

            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(
                    self._process.wait(),
                    timeout=grace_period_ms / 1000.0,
                )
                logger.info("Template worker shut down gracefully")
            except asyncio.TimeoutError:
                logger.warning("Template worker did not shutdown, killing")
                self._process.terminate()
                await asyncio.sleep(1)
                if self._process.returncode is None:
                    self._process.kill()

        except Exception as e:
            logger.error(f"Error stopping template worker: {e}")
            if self._process and self._process.returncode is None:
                self._process.kill()

        finally:
            if self._reader_task:
                self._reader_task.cancel()
                try:
                    await self._reader_task
                except asyncio.CancelledError:
                    pass

            self._process = None
            self._reader_task = None
            self._status = ProcessStatus.STOPPED

            for future in self._pending_requests.values():
                if not future.done():
                    future.cancel()
            self._pending_requests.clear()

    async def execute_template(
        self,
        template_id: str,
        definition: Dict[str, Any],
        input_params: Dict[str, Any],
        execution_id: str,
        config: Optional[Dict[str, Any]] = None,
        timeout_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute a template in the worker.

        Args:
            template_id: Template ID
            definition: Template definition with steps
            input_params: Input parameters
            execution_id: Unique execution ID
            config: Execution configuration
            timeout_ms: Timeout (uses config default if not specified)

        Returns:
            Execution result

        Raises:
            Exception: If execution fails
        """
        if not self.is_ready:
            if not await self.start():
                return {
                    "ok": False,
                    "error": "Template worker failed to start",
                }

        timeout = timeout_ms or self.config.default_timeout_ms
        request_id = self._next_request_id()

        future: asyncio.Future = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            self._status = ProcessStatus.BUSY

            msg = ProtocolEncoder.encode_execute_template(
                template_id=template_id,
                definition=definition,
                input_params=input_params,
                execution_id=execution_id,
                config=config or {},
                request_id=request_id,
                timeout_ms=timeout,
            )
            await self._send(msg)

            try:
                response = await asyncio.wait_for(
                    future,
                    timeout=timeout / 1000.0,
                )
                return ProtocolDecoder.extract_result(response)

            except asyncio.TimeoutError:
                return {
                    "ok": False,
                    "error": f"Template execution timed out after {timeout}ms",
                    "error_code": "TIMEOUT",
                }

        finally:
            self._pending_requests.pop(request_id, None)
            if self._status == ProcessStatus.BUSY:
                self._status = ProcessStatus.READY

    async def ping(self, timeout_ms: int = 5000) -> bool:
        """
        Health check the worker.

        Args:
            timeout_ms: Timeout for ping response

        Returns:
            True if healthy, False otherwise
        """
        if self._process is None or self._process.returncode is not None:
            return False

        request_id = self._next_request_id()
        future: asyncio.Future = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            msg = ProtocolEncoder.encode_ping(request_id)
            await self._send(msg)

            await asyncio.wait_for(future, timeout=timeout_ms / 1000.0)
            return True

        except (asyncio.TimeoutError, Exception):
            return False

        finally:
            self._pending_requests.pop(request_id, None)

    async def _handshake(self) -> bool:
        """Perform protocol handshake."""
        request_id = self._next_request_id()
        future: asyncio.Future = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            msg = ProtocolEncoder.encode_handshake(
                PROTOCOL_VERSION,
                "startup",
                request_id,
            )
            await self._send(msg)

            response = await asyncio.wait_for(
                future,
                timeout=self.config.handshake_timeout_ms / 1000.0,
            )

            if response.is_success:
                result = response.result or {}
                worker_version = result.get("workerVersion", "unknown")
                logger.info(f"Template worker handshake complete (v{worker_version})")
                return True
            else:
                logger.error(f"Handshake failed: {response.error}")
                return False

        except asyncio.TimeoutError:
            logger.error("Handshake timeout")
            return False

        except Exception as e:
            logger.error(f"Handshake error: {e}")
            return False

        finally:
            self._pending_requests.pop(request_id, None)

    async def _send(self, message: str):
        """Send message to worker stdin."""
        if self._process and self._process.stdin:
            data = (message + "\n").encode("utf-8")
            self._process.stdin.write(data)
            await self._process.stdin.drain()

    async def _read_stdout(self):
        """Read and process messages from worker stdout."""
        if not self._process or not self._process.stdout:
            return

        try:
            while True:
                line = await self._process.stdout.readline()
                if not line:
                    await self._handle_crash()
                    break

                try:
                    data = line.decode("utf-8").strip()
                    if not data:
                        continue

                    # Check if it's a notification (no id)
                    if ProtocolDecoder.is_notification(data):
                        notification = ProtocolDecoder.decode_notification(data)
                        handler = self._notification_handlers.get(notification.method)
                        if handler:
                            try:
                                handler(notification.params)
                            except Exception as e:
                                logger.error(f"Notification handler error: {e}")
                    else:
                        response = ProtocolDecoder.decode_response(data)
                        future = self._pending_requests.get(response.id)
                        if future and not future.done():
                            future.set_result(response)

                except Exception as e:
                    logger.error(f"Error processing worker output: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Reader task error: {e}")
            await self._handle_crash()

    async def _handle_crash(self):
        """Handle worker crash."""
        exit_code = self._process.returncode if self._process else None
        logger.error(f"Template worker crashed (exit: {exit_code})")

        self._restart_times.append(time.time())
        cutoff = time.time() - self.restart_policy.restart_window_seconds
        self._restart_times = [t for t in self._restart_times if t > cutoff]

        if len(self._restart_times) >= self.restart_policy.max_restarts:
            self._status = ProcessStatus.UNHEALTHY
            self._unhealthy_until = time.time() + self.restart_policy.unhealthy_cooldown_seconds
            logger.error(
                f"Template worker marked unhealthy "
                f"(cooldown: {self.restart_policy.unhealthy_cooldown_seconds}s)"
            )
        else:
            self._status = ProcessStatus.STOPPED

        for future in self._pending_requests.values():
            if not future.done():
                future.set_exception(Exception(f"Worker crashed (exit: {exit_code})"))
        self._pending_requests.clear()

        self._process = None


class TemplateRuntime:
    """
    High-level interface for template execution.

    Manages worker pool and provides simple execute API.
    """

    _instance: Optional["TemplateRuntime"] = None

    def __init__(self, config: Optional[TemplateProcessConfig] = None):
        """Initialize runtime with optional process configuration."""
        self.config = config or TemplateProcessConfig()
        self._worker: Optional[TemplateProcess] = None
        self._lock = asyncio.Lock()

        # Notification handlers
        self._step_progress_handlers: List[Callable] = []

    @classmethod
    def get_instance(cls, config: Optional[TemplateProcessConfig] = None) -> "TemplateRuntime":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing)."""
        if cls._instance:
            asyncio.create_task(cls._instance.shutdown())
        cls._instance = None

    def on_step_progress(self, handler: Callable):
        """Register a step progress handler."""
        self._step_progress_handlers.append(handler)

    async def _get_worker(self) -> TemplateProcess:
        """Get or create worker."""
        async with self._lock:
            if self._worker is None:
                self._worker = TemplateProcess(self.config)

                # Register notification handlers
                def handle_step_progress(params):
                    for handler in self._step_progress_handlers:
                        try:
                            handler(params)
                        except Exception as e:
                            logger.error(f"Step progress handler error: {e}")

                self._worker.on_notification("step_progress", handle_step_progress)

            return self._worker

    async def execute_template(
        self,
        template_id: str,
        definition: Dict[str, Any],
        input_params: Dict[str, Any],
        execution_id: str,
        config: Optional[Dict[str, Any]] = None,
        timeout_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute a template.

        Args:
            template_id: Template ID
            definition: Template definition with steps
            input_params: Input parameters
            execution_id: Unique execution ID
            config: Execution configuration
            timeout_ms: Timeout in milliseconds

        Returns:
            Execution result dict with 'ok' and 'data' or 'error'
        """
        worker = await self._get_worker()
        return await worker.execute_template(
            template_id=template_id,
            definition=definition,
            input_params=input_params,
            execution_id=execution_id,
            config=config,
            timeout_ms=timeout_ms,
        )

    async def health_check(self) -> bool:
        """Check if runtime is healthy."""
        if self._worker is None:
            return True  # Not started yet, considered healthy

        return await self._worker.ping()

    async def shutdown(self):
        """Shutdown the runtime and worker."""
        if self._worker:
            await self._worker.stop()
            self._worker = None


def get_template_runtime(config: Optional[TemplateProcessConfig] = None) -> TemplateRuntime:
    """Get the global template runtime instance."""
    return TemplateRuntime.get_instance(config)
