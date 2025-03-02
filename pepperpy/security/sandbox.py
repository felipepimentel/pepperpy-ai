"""Sandbox module for secure code execution.

This module provides a secure sandbox environment for executing untrusted code.
It uses process isolation and resource limits to prevent malicious code execution.
"""

import asyncio
import logging
import resource
import signal
from pathlib import Path
from typing import Any, Dict, Optional

from pepperpy.core.base import Lifecycle
from pepperpy.security.errors import SecurityError

logger = logging.getLogger(__name__)


class SandboxConfig:
    """Configuration for sandbox execution."""

    def __init__(
        self,
        max_memory: int = 512 * 1024 * 1024,  # 512MB
        max_cpu_time: int = 30,  # 30 seconds
        max_processes: int = 1,
        allowed_modules: Optional[set[str]] = None,
    ):
        """Initialize sandbox configuration.

        Args:
            max_memory: Maximum memory usage in bytes
            max_cpu_time: Maximum CPU time in seconds
            max_processes: Maximum number of processes
            allowed_modules: Set of allowed Python modules
        """
        self.max_memory = max_memory
        self.max_cpu_time = max_cpu_time
        self.max_processes = max_processes
        self.allowed_modules = allowed_modules or {
            "builtins",
            "math",
            "random",
            "time",
            "json",
            "typing",
        }


class Sandbox(Lifecycle):
    """Secure sandbox for code execution."""

    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        """Initialize sandbox.

        Args:
            config: Optional sandbox configuration
        """
        super().__init__()
        self.config = config or SandboxConfig()
        self._temp_dir = Path("/tmp/pepperpy_sandbox")

    async def initialize(self) -> None:
        """Initialize sandbox environment."""
        try:
            # Create temp directory
            self._temp_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Sandbox initialized")

        except Exception as e:
            raise SecurityError(f"Failed to initialize sandbox: {e}") from e

    async def cleanup(self) -> None:
        """Clean up sandbox resources."""
        try:
            # Remove temp files
            if self._temp_dir.exists():
                for file in self._temp_dir.glob("*"):
                    file.unlink()
                self._temp_dir.rmdir()
            logger.info("Sandbox cleaned up")

        except Exception as e:
            logger.error(f"Failed to cleanup sandbox: {e}")

    def _set_resource_limits(self) -> None:
        """Set resource limits for sandbox process."""
        # Set memory limit
        resource.setrlimit(
            resource.RLIMIT_AS,
            (self.config.max_memory, self.config.max_memory),
        )

        # Set CPU time limit
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (self.config.max_cpu_time, self.config.max_cpu_time),
        )

        # Set process limit
        resource.setrlimit(
            resource.RLIMIT_NPROC,
            (self.config.max_processes, self.config.max_processes),
        )

    async def execute(
        self,
        code: str,
        timeout: int = 30,
        artifact_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute code in sandbox.

        Args:
            code: Code to execute
            timeout: Execution timeout in seconds
            artifact_id: Optional artifact ID for logging

        Returns:
            Dict[str, Any]: Execution results

        Raises:
            SecurityError: If execution fails or times out
        """
        try:
            # Create temp file for code
            code_file = self._temp_dir / f"{artifact_id or 'code'}.py"
            with open(code_file, "w") as f:
                f.write(code)

            # Create subprocess for isolation
            process = await asyncio.create_subprocess_exec(
                "python",
                str(code_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=self._set_resource_limits,
            )

            try:
                # Wait for process with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )

                # Check return code
                if process.returncode != 0:
                    raise SecurityError(
                        "Code execution failed",
                        details={
                            "return_code": process.returncode,
                            "stderr": stderr.decode(),
                        },
                    )

                return {
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "return_code": process.returncode,
                }

            except asyncio.TimeoutError:
                # Kill process on timeout
                try:
                    process.send_signal(signal.SIGKILL)
                    await process.wait()
                except Exception:
                    pass
                raise SecurityError("Code execution timed out") from None

            finally:
                # Clean up temp file
                code_file.unlink()

        except SecurityError:
            raise
        except Exception as e:
            raise SecurityError(f"Failed to execute code: {e}") from e
