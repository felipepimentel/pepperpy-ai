"""Health checking functionality.

This module provides tools for checking system health.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class HealthCheck(ABC):
    """Base class for health checks."""

    def __init__(self, name: str, timeout: float = 5.0) -> None:
        """Initialize health check.

        Args:
            name: Check name
            timeout: Check timeout in seconds
        """
        self.name = name
        self.timeout = timeout
        self.last_check_time = 0.0
        self.last_status: dict[str, Any] = {}

    @abstractmethod
    async def check(self) -> dict[str, Any]:
        """Run health check.

        Returns:
            Check results
        """
        pass

    async def run(self) -> dict[str, Any]:
        """Run check with timeout.

        Returns:
            Check results
        """
        try:
            # Create task with timeout
            result = await asyncio.wait_for(self.check(), timeout=self.timeout)
            status = {
                "status": "healthy",
                "timestamp": time.time(),
                "result": result,
            }
        except TimeoutError:
            status = {
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": f"Check timed out after {self.timeout} seconds",
            }
        except Exception as e:
            status = {
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e),
            }

        self.last_check_time = status["timestamp"]
        self.last_status = status
        return status


class DatabaseCheck(HealthCheck):
    """Health check for database connectivity."""

    def __init__(self, db_check: Callable[[], bool], name: str = "database") -> None:
        """Initialize database check.

        Args:
            db_check: Function to check database connectivity
            name: Check name
        """
        super().__init__(name)
        self._check_func = db_check

    async def check(self) -> dict[str, Any]:
        """Check database connectivity.

        Returns:
            Check results
        """
        is_healthy = await asyncio.to_thread(self._check_func)
        return {"connected": is_healthy}


class RedisCheck(HealthCheck):
    """Health check for Redis connectivity."""

    def __init__(self, redis_check: Callable[[], bool], name: str = "redis") -> None:
        """Initialize Redis check.

        Args:
            redis_check: Function to check Redis connectivity
            name: Check name
        """
        super().__init__(name)
        self._check_func = redis_check

    async def check(self) -> dict[str, Any]:
        """Check Redis connectivity.

        Returns:
            Check results
        """
        is_healthy = await asyncio.to_thread(self._check_func)
        return {"connected": is_healthy}


class HealthChecker:
    """Manages health checks."""

    def __init__(self) -> None:
        """Initialize health checker."""
        self._checks: dict[str, HealthCheck] = {}

    def add_check(self, check: HealthCheck) -> None:
        """Add a health check.

        Args:
            check: Health check to add
        """
        self._checks[check.name] = check

    def remove_check(self, name: str) -> None:
        """Remove a health check.

        Args:
            name: Name of check to remove
        """
        self._checks.pop(name, None)

    async def check_all(self) -> dict[str, Any]:
        """Run all health checks.

        Returns:
            Results of all checks
        """
        results = {}
        overall_status = "healthy"

        for name, check in self._checks.items():
            status = await check.run()
            results[name] = status
            if status["status"] != "healthy":
                overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "checks": results,
        }

    async def check_one(self, name: str) -> dict[str, Any]:
        """Run a specific health check.

        Args:
            name: Name of check to run

        Returns:
            Check results
        """
        if name not in self._checks:
            return {
                "status": "unknown",
                "timestamp": time.time(),
                "error": f"No health check named {name}",
            }
        return await self._checks[name].run()

    def get_last_status(self, name: str | None = None) -> dict[str, Any]:
        """Get last status of health checks.

        Args:
            name: Optional specific check name

        Returns:
            Last check status(es)
        """
        if name is not None:
            check = self._checks.get(name)
            if not check:
                return {
                    "status": "unknown",
                    "timestamp": time.time(),
                    "error": f"No health check named {name}",
                }
            return check.last_status

        results = {}
        overall_status = "healthy"

        for name, check in self._checks.items():
            status = check.last_status
            results[name] = status
            if status.get("status") != "healthy":
                overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "checks": results,
        }


__all__ = ["DatabaseCheck", "HealthCheck", "HealthChecker", "RedisCheck"]
