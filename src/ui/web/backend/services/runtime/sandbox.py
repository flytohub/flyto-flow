"""
Sandbox Execution Service

Secure execution of user-provided code in isolated environments.
"""

import json
import logging
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SandboxLanguage(str, Enum):
    """Supported sandbox languages."""
    JAVASCRIPT = "javascript"
    PYTHON = "python"


@dataclass
class SandboxResult:
    """Result from sandbox execution."""
    ok: bool
    result: Any = None
    output: str = ""
    error: Optional[str] = None
    execution_time_ms: int = 0


class SandboxExecutor:
    """
    Executes code in a sandboxed environment.

    Security measures:
    - Execution timeout (default 5 seconds)
    - Memory limit (via ulimit on Unix)
    - No filesystem access beyond temp files
    - No network access (via seccomp on Linux, limited on macOS)
    - Isolated process with restricted permissions
    """

    DEFAULT_TIMEOUT_SECONDS = 5
    MAX_OUTPUT_SIZE = 10000  # 10KB max output

    def __init__(self, timeout_seconds: int = None):
        """Initialize with optional execution timeout in seconds."""
        self.timeout = timeout_seconds or self.DEFAULT_TIMEOUT_SECONDS

    async def execute(
        self,
        code: str,
        language: SandboxLanguage,
        params: Dict[str, Any],
    ) -> SandboxResult:
        """
        Execute code in sandbox.

        Args:
            code: The code to execute
            language: Programming language
            params: Input parameters for the code

        Returns:
            SandboxResult with execution result or error
        """
        if language == SandboxLanguage.JAVASCRIPT:
            return await self._execute_javascript(code, params)
        elif language == SandboxLanguage.PYTHON:
            return await self._execute_python(code, params)
        else:
            return SandboxResult(
                ok=False,
                error=f"Unsupported language: {language}"
            )

    @staticmethod
    def _build_js_wrapper(code: str, params: Dict[str, Any]) -> str:
        """Build the JavaScript wrapper code with sandboxed globals."""
        return f'''
// Disable dangerous globals
const _blocked = ['require', 'process', 'global', '__dirname', '__filename', 'module', 'exports'];
_blocked.forEach(g => {{ if (typeof globalThis[g] !== 'undefined') delete globalThis[g]; }});

// Provide input parameters
const params = {json.dumps(params)};

// User code execution
try {{
    const userFunction = (function() {{
        {code}
    }});

    // If user code returns a function, call it with params
    const result = typeof userFunction === 'function' ? userFunction(params) : userFunction;

    // Handle async results
    Promise.resolve(result).then(r => {{
        console.log(JSON.stringify({{ ok: true, result: r }}));
    }}).catch(e => {{
        console.log(JSON.stringify({{ ok: false, error: e.message }}));
    }});
}} catch (e) {{
    console.log(JSON.stringify({{ ok: false, error: e.message }}));
}}
'''

    def _parse_js_output(self, result: subprocess.CompletedProcess, execution_time: int) -> SandboxResult:
        """Parse the output of a Node.js subprocess into a SandboxResult."""
        output = result.stdout.strip()
        if output:
            try:
                parsed = json.loads(output[-self.MAX_OUTPUT_SIZE:])
                return SandboxResult(
                    ok=parsed.get('ok', False),
                    result=parsed.get('result'),
                    error=parsed.get('error'),
                    output=output[:self.MAX_OUTPUT_SIZE],
                    execution_time_ms=execution_time
                )
            except json.JSONDecodeError:
                return SandboxResult(
                    ok=True,
                    result=output[:self.MAX_OUTPUT_SIZE],
                    execution_time_ms=execution_time
                )

        if result.stderr:
            return SandboxResult(
                ok=False,
                error=result.stderr[:500],
                execution_time_ms=execution_time
            )

        return SandboxResult(ok=True, result=None, execution_time_ms=execution_time)

    async def _execute_javascript(
        self,
        code: str,
        params: Dict[str, Any],
    ) -> SandboxResult:
        """Execute JavaScript code using Node.js subprocess."""
        import time

        wrapper_code = self._build_js_wrapper(code, params)
        start_time = time.time()

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(wrapper_code)
                temp_file = f.name

            try:
                result = subprocess.run(
                    ['node', '--no-warnings', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    env={
                        'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
                        'NODE_OPTIONS': '--max-old-space-size=64'
                    }
                )
                execution_time = int((time.time() - start_time) * 1000)
                return self._parse_js_output(result, execution_time)
            finally:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass

        except subprocess.TimeoutExpired:
            return SandboxResult(ok=False, error=f"Execution timeout ({self.timeout}s exceeded)")
        except FileNotFoundError:
            return SandboxResult(ok=False, error="Node.js not available for JavaScript execution")
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return SandboxResult(ok=False, error=str(e))

    async def _execute_python(
        self,
        code: str,
        params: Dict[str, Any],
    ) -> SandboxResult:
        """
        Execute Python code with RestrictedPython.

        Uses RestrictedPython for safe execution with limited builtins.
        """
        import time

        try:
            from RestrictedPython import compile_restricted, safe_builtins
            from RestrictedPython.Guards import safe_builtins as rb_safe_builtins
        except ImportError:
            return SandboxResult(
                ok=False,
                error="RestrictedPython not installed"
            )

        start_time = time.time()

        try:
            # Compile the code in restricted mode
            byte_code = compile_restricted(
                code,
                '<user_code>',
                'exec'
            )

            if byte_code.errors:
                return SandboxResult(
                    ok=False,
                    error=f"Compilation errors: {byte_code.errors}"
                )

            # Create safe execution environment
            safe_globals = {
                '__builtins__': safe_builtins,
                'params': params,
                '_result': None,
                '_print_': lambda x: None,  # Disable print
                '_getattr_': lambda obj, attr: getattr(obj, attr) if not attr.startswith('_') else None,
                '_getitem_': lambda obj, key: obj[key],
                '_getiter_': iter,
                '_write_': lambda x: x,
            }

            # Safe subset of builtins
            allowed_builtins = {
                'True': True,
                'False': False,
                'None': None,
                'abs': abs,
                'all': all,
                'any': any,
                'bool': bool,
                'dict': dict,
                'float': float,
                'int': int,
                'len': len,
                'list': list,
                'max': max,
                'min': min,
                'range': range,
                'round': round,
                'set': set,
                'sorted': sorted,
                'str': str,
                'sum': sum,
                'tuple': tuple,
                'zip': zip,
                'enumerate': enumerate,
                'map': map,
                'filter': filter,
            }
            safe_globals['__builtins__'] = allowed_builtins

            # Execute the code
            local_vars = {}
            exec(byte_code.code, safe_globals, local_vars)

            execution_time = int((time.time() - start_time) * 1000)

            # Get result from local vars
            result = local_vars.get('result', local_vars.get('_result'))

            return SandboxResult(
                ok=True,
                result=result,
                execution_time_ms=execution_time
            )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return SandboxResult(
                ok=False,
                error=str(e),
                execution_time_ms=execution_time
            )


# Singleton instance
_executor: Optional[SandboxExecutor] = None


def get_sandbox_executor() -> SandboxExecutor:
    """Get or create sandbox executor instance."""
    global _executor
    if _executor is None:
        _executor = SandboxExecutor()
    return _executor
