"""Health check module for Pepperpy.

This module provides health checking capabilities:
- Component health checks
- System health probes
- Health status reporting
- Readiness and liveness probes
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState

logger = logging.getLogger(__name__)


class HealthStatus(BaseModel):
    """Health status model."""

    status: str = Field(
        default="unknown",
        description="Health status (healthy, unhealthy, degraded)",
    )
    message: Optional[str] = Field(
        default=None,
        description="Status message",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Status timestamp",
    )
    details: Dict = Field(
        default_factory=dict,
        description="Status details",
    )


class HealthCheck(BaseModel):
    """Health check configuration."""

    name: str = Field(
        description="Check name",
    )
    type: str = Field(
        description="Check type (component, system, custom)",
    )
    interval: int = Field(
        default=60,
        description="Check interval in seconds",
    )
    timeout: int = Field(
        default=10,
        description="Check timeout in seconds",
    )
    retries: int = Field(
        default=3,
        description="Number of retries",
    )


class HealthManager(Lifecycle):
    """Manages health checks."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        """Initialize health manager.

        Args:
            config: Optional health configuration
        """
        super().__init__()
        self.config = config or {}
        self._checks: Dict[str, HealthCheck] = {}
        self._status: Dict[str, HealthStatus] = {}
        self._tasks: List[asyncio.Task] = []
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize health manager.

        This sets up health checks and starts monitoring.
        """
        try:
            # Load checks from config
            for check_config in self.config.get("checks", []):
                check = HealthCheck(**check_config)
                self._checks[check.name] = check

            # Start monitoring tasks
            for check in self._checks.values():
                task = asyncio.create_task(self._monitor_check(check))
                self._tasks.append(task)

            self._state = ComponentState.RUNNING
            logger.info("Health manager initialized")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize health manager: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up health manager."""
        try:
            # Cancel monitoring tasks
            for task in self._tasks:
                task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)

            # Clear state
            self._checks.clear()
            self._status.clear()
            self._tasks.clear()
            self._state = ComponentState.UNREGISTERED

            logger.info("Health manager cleaned up")

        except Exception as e:
            logger.error(f"Failed to cleanup health manager: {e}")
            raise

    async def _monitor_check(self, check: HealthCheck) -> None:
        """Monitor a health check.

        Args:
            check: Health check to monitor
        """
        while True:
            try:
                # Run check with timeout
                status = await asyncio.wait_for(
                    self._run_check(check),
                    timeout=check.timeout,
                )
                self._status[check.name] = status

            except asyncio.TimeoutError:
                self._status[check.name] = HealthStatus(
                    status="unhealthy",
                    message=f"Check timed out after {check.timeout}s",
                )

            except Exception as e:
                self._status[check.name] = HealthStatus(
                    status="unhealthy",
                    message=str(e),
                )

            # Wait for next interval
            await asyncio.sleep(check.interval)

    async def _run_check(self, check: HealthCheck) -> HealthStatus:
        """Run a health check.

        Args:
            check: Health check to run

        Returns:
            HealthStatus: Check result
        """
        # Import check module dynamically
        module_name = f"pepperpy.monitoring.health.checks.{check.type}"
        try:
            module = __import__(module_name, fromlist=["check"])
            result = await module.check()
            return HealthStatus(
                status="healthy",
                message="Check passed",
                details=result,
            )
        except ImportError:
            return HealthStatus(
                status="unknown",
                message=f"Check type not found: {check.type}",
            )
        except Exception as e:
            return HealthStatus(
                status="unhealthy",
                message=str(e),
            )

    def get_status(self, check_name: Optional[str] = None) -> Dict[str, HealthStatus]:
        """Get health status.

        Args:
            check_name: Optional check name to filter

        Returns:
            Dict[str, HealthStatus]: Health status by check name
        """
        if check_name:
            return {check_name: self._status.get(check_name, HealthStatus())}
        return self._status.copy()
