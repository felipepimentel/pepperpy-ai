"""Health checks functionality for PepperPy observability.

This module provides functionality for performing health checks on various
components and services within PepperPy.
"""

import asyncio
import logging
import os
import platform
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil

from pepperpy.common.types import ComponentState
from pepperpy.hub.manager import HubManager
from pepperpy.observability.metrics.manager import MetricsManager

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status indicators."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Container for health check results."""

    component: str
    status: HealthStatus
    timestamp: datetime
    details: Dict[str, Any]
    message: Optional[str] = None


class HealthCheck:
    """Base class for health checks."""

    def __init__(self, component: str):
        self.component = component

    def check(self) -> HealthCheckResult:
        """Perform the health check."""
        raise NotImplementedError("Health check implementation required")


class HealthChecker:
    """Manager for running health checks."""

    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}
        self._last_results: Dict[str, HealthCheckResult] = {}

    def register_check(self, check: HealthCheck) -> None:
        """Register a new health check."""
        self._checks[check.component] = check

    def run_check(self, component: str) -> Optional[HealthCheckResult]:
        """Run a specific health check."""
        check = self._checks.get(component)
        if not check:
            return None

        result = check.check()
        self._last_results[component] = result
        return result

    def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all registered health checks."""
        results = []
        for check in self._checks.values():
            result = check.check()
            self._last_results[check.component] = result
            results.append(result)
        return results

    def get_last_result(self, component: str) -> Optional[HealthCheckResult]:
        """Get the last result for a specific component."""
        return self._last_results.get(component)

    def get_all_results(self) -> Dict[str, HealthCheckResult]:
        """Get all last results."""
        return self._last_results.copy()


class SystemHealthCheck(HealthCheck):
    """Health check for system resources."""

    def __init__(self):
        super().__init__("system")
        self._thresholds = {
            "cpu_percent": 90.0,
            "memory_percent": 90.0,
            "disk_percent": 95.0,
        }

    def check(self) -> HealthCheckResult:
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
            }

            status = HealthStatus.HEALTHY
            messages = []

            if cpu_percent > self._thresholds["cpu_percent"]:
                status = HealthStatus.DEGRADED
                messages.append(f"CPU usage is high: {cpu_percent}%")

            if memory.percent > self._thresholds["memory_percent"]:
                status = HealthStatus.DEGRADED
                messages.append(f"Memory usage is high: {memory.percent}%")

            if disk.percent > self._thresholds["disk_percent"]:
                status = HealthStatus.DEGRADED
                messages.append(f"Disk usage is high: {disk.percent}%")

            return HealthCheckResult(
                component=self.component,
                status=status,
                timestamp=datetime.now(),
                details=details,
                message="; ".join(messages) if messages else None,
            )

        except Exception as e:
            return HealthCheckResult(
                component=self.component,
                status=HealthStatus.UNHEALTHY,
                timestamp=datetime.now(),
                details={"error": str(e)},
                message=f"Health check failed: {str(e)}",
            )


async def check_system() -> Dict:
    """Check system health.

    Returns:
        Dict: System health metrics
    """
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
    }


async def check_components() -> Dict:
    """Check component health.

    Returns:
        Dict: Component health status
    """
    # Get component states
    hub = HubManager()
    metrics = MetricsManager()

    return {
        "hub": hub.state == ComponentState.RUNNING,
        "metrics": metrics.state == ComponentState.RUNNING,
    }


async def check_network() -> Dict:
    """Check network connectivity.

    Returns:
        Dict: Network health status
    """
    # Check basic connectivity
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping",
            "-c",
            "1",
            "-W",
            "2",
            "8.8.8.8",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        network_ok = proc.returncode == 0
    except Exception:
        network_ok = False

    # Check DNS resolution
    try:
        proc = await asyncio.create_subprocess_exec(
            "nslookup",
            "google.com",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        dns_ok = proc.returncode == 0
    except Exception:
        dns_ok = False

    return {
        "network": network_ok,
        "dns": dns_ok,
    }


async def check_storage() -> Dict:
    """Check storage health.

    Returns:
        Dict: Storage health status
    """
    # Check temp directory
    temp_ok = os.access("/tmp", os.W_OK)

    # Check workspace directory
    workspace = os.environ.get("PEPPERPY_WORKSPACE", ".")
    workspace_ok = os.access(workspace, os.W_OK)

    # Check available space
    try:
        disk = psutil.disk_usage("/")
        space_ok = disk.free > 1024 * 1024 * 1024  # 1GB
    except Exception:
        space_ok = False

    return {
        "temp_writable": temp_ok,
        "workspace_writable": workspace_ok,
        "space_available": space_ok,
    }
