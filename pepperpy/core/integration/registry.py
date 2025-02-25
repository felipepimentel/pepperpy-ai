"""Service registry for component discovery and management."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pepperpy.core.errors import NotFoundError, StateError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.metrics import MetricsCollector


class ServiceStatus:
    """Service status enumeration."""

    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ServiceInfo:
    """Service information container."""

    name: str
    status: str  # Using str type for status
    metadata: dict[str, Any]
    last_heartbeat: datetime
    instance: Any


class ServiceRegistry(Lifecycle):
    """Centralized service registry for component management and discovery.

    This registry maintains information about all active services, including:
    - Service status and health
    - Service metadata
    - Service discovery
    - Health monitoring
    """

    def __init__(
        self,
        heartbeat_timeout: int = 60,
        cleanup_interval: int = 30,
        metrics: MetricsCollector | None = None,
    ) -> None:
        """Initialize the service registry.

        Args:
            heartbeat_timeout: Seconds until service is marked as failed
            cleanup_interval: Seconds between cleanup runs
            metrics: Optional metrics collector
        """
        super().__init__()
        self._services: dict[str, ServiceInfo] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_timeout = datetime.timedelta(seconds=heartbeat_timeout)
        self._cleanup_interval = cleanup_interval
        self._metrics = metrics
        self._logger = logging.getLogger(__name__)

    async def _initialize(self) -> None:
        """Initialize the registry.

        This starts the cleanup task for removing expired services.
        """
        self._logger.info("Initializing service registry")
        asyncio.create_task(self._cleanup_loop())

    async def _cleanup(self) -> None:
        """Clean up registry resources."""
        self._logger.info("Cleaning up service registry")
        async with self._lock:
            self._services.clear()

    async def register(self, service: ServiceInfo) -> None:
        """Register a service with the registry.

        Args:
            service: Service information to register

        Raises:
            StateError: If registry is not running
        """
        if not self.is_running():
            raise StateError("Registry is not running")

        async with self._lock:
            self._services[service.name] = service
            self._logger.info(f"Registered service: {service.name}")

    async def unregister(self, name: str) -> None:
        """Unregister a service from the registry.

        Args:
            name: Name of service to unregister

        Raises:
            StateError: If registry is not running
            NotFoundError: If service is not found
        """
        if not self.is_running():
            raise StateError("Registry is not running")

        async with self._lock:
            if name not in self._services:
                raise NotFoundError(f"Service not found: {name}")

            del self._services[name]
            self._logger.info(f"Unregistered service: {name}")

    async def get_service(self, name: str) -> ServiceInfo:
        """Get information about a registered service.

        Args:
            name: Name of service to get

        Returns:
            Service information

        Raises:
            StateError: If registry is not running
            NotFoundError: If service is not found
        """
        if not self.is_running():
            raise StateError("Registry is not running")

        async with self._lock:
            if name not in self._services:
                raise NotFoundError(f"Service not found: {name}")

            return self._services[name]

    async def list_services(self) -> set[str]:
        """Get names of all registered services.

        Returns:
            Set of service names

        Raises:
            StateError: If registry is not running
        """
        if not self.is_running():
            raise StateError("Registry is not running")

        async with self._lock:
            return set(self._services.keys())

    async def update_status(self, name: str, status: str) -> None:
        """Update the status of a registered service.

        Args:
            name: Name of service to update
            status: New service status

        Raises:
            StateError: If registry is not running
            NotFoundError: If service is not found
        """
        if not self.is_running():
            raise StateError("Registry is not running")

        async with self._lock:
            if name not in self._services:
                raise NotFoundError(f"Service not found: {name}")

            service = self._services[name]
            service.status = status
            service.last_heartbeat = datetime.now()

            self._logger.info(f"Updated service status: {name} -> {status}")

    async def heartbeat(self, name: str) -> None:
        """Update the last heartbeat time for a service.

        Args:
            name: Name of service to update

        Raises:
            StateError: If registry is not running
            NotFoundError: If service is not found
        """
        if not self.is_running():
            raise StateError("Registry is not running")

        async with self._lock:
            if name not in self._services:
                raise NotFoundError(f"Service not found: {name}")

            self._services[name].last_heartbeat = datetime.now()

    async def _cleanup_loop(self) -> None:
        """Background task that removes expired services."""
        while True:
            try:
                if not self.is_running():
                    break

                async with self._lock:
                    now = datetime.now()
                    failed_count = 0

                    for service in self._services.values():
                        if (now - service.last_heartbeat) > self._heartbeat_timeout:
                            service.status = ServiceStatus.ERROR
                            failed_count += 1
                            self._logger.warning(
                                f"Service {service.name} failed heartbeat check"
                            )

                    if failed_count > 0:
                        self._logger.warning(
                            f"Found {failed_count} services with failed heartbeats"
                        )

                await asyncio.sleep(self._cleanup_interval)

            except Exception as e:
                self._logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause before retry
