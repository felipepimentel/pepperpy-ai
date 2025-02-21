"""Built-in health checks for Pepperpy.

This module provides built-in health checks:
- Component health checks
- System resource checks
- Network connectivity checks
- Storage health checks
"""

import asyncio
import logging
import os
import platform
from typing import Dict

import psutil

from pepperpy.core.types import ComponentState
from pepperpy.hub.manager import HubManager
from pepperpy.monitoring.metrics import MetricsManager

logger = logging.getLogger(__name__)


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
