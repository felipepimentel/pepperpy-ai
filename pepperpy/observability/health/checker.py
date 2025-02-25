"""Health check implementation.

This module provides a health checking system that monitors
component health and dependencies.

Example:
    >>> checker = HealthChecker()
    >>> health = await checker.check_health("api", ["database", "cache"])
    >>> assert health.status == HealthStatus.HEALTHY
    >>> status = await checker.get_health_status()
    >>> assert len(status) > 0
"""

import time

from ..errors import HealthCheckError
from ..types import HealthCheck, HealthStatus


class HealthChecker:
    """Health checker implementation.

    This class implements health checks for system components.
    It provides methods for checking component health and dependencies.

    Attributes:
        _checks: Dictionary mapping component names to their health checks
        _dependencies: Dictionary mapping components to their dependencies

    Example:
        >>> checker = HealthChecker()
        >>> health = await checker.check_health("api", ["database", "cache"])
        >>> assert health.status == HealthStatus.HEALTHY
        >>> status = await checker.get_health_status()
        >>> assert len(status) > 0
    """

    def __init__(self) -> None:
        """Initialize health checker."""
        self._checks: dict[str, HealthCheck] = {}
        self._dependencies: dict[str, list[str]] = {}

    async def check_health(
        self,
        name: str,
        dependencies: list[str] | None = None,
    ) -> HealthCheck:
        """Perform a health check.

        Args:
            name: Name of the component to check
            dependencies: Optional list of dependencies to check

        Returns:
            The health check result

        Raises:
            HealthCheckError: If health check fails
        """
        try:
            # Check dependencies first
            dep_status = HealthStatus.HEALTHY
            dep_details = {}

            if dependencies:
                self._dependencies[name] = dependencies
                for dep in dependencies:
                    try:
                        dep_check = await self.check_health(dep)
                        dep_details[dep] = {
                            "status": dep_check.status,
                            "details": dep_check.details,
                        }
                        if dep_check.status == HealthStatus.UNHEALTHY:
                            dep_status = HealthStatus.UNHEALTHY
                            break
                        elif dep_check.status == HealthStatus.DEGRADED:
                            dep_status = HealthStatus.DEGRADED
                    except Exception as e:
                        dep_details[dep] = {
                            "status": HealthStatus.UNHEALTHY,
                            "error": str(e),
                        }
                        dep_status = HealthStatus.UNHEALTHY

            # Create health check result
            check = HealthCheck(
                name=name,
                status=dep_status,
                timestamp=time.time(),
                details={
                    "dependencies": dep_details,
                },
                dependencies=dependencies,
            )

            self._checks[name] = check
            return check

        except Exception as e:
            raise HealthCheckError(f"Failed to check health: {e}")

    async def get_health_status(self) -> dict[str, HealthCheck]:
        """Get health status of all components.

        Returns:
            Dictionary mapping component names to their health check results

        Raises:
            HealthCheckError: If health status retrieval fails
        """
        try:
            # Update all health checks
            for name in list(self._checks.keys()):
                await self.check_health(
                    name,
                    self._dependencies.get(name),
                )
            return self._checks

        except Exception as e:
            raise HealthCheckError(f"Failed to get health status: {e}")
