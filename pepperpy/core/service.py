"""Base service implementation."""

import asyncio
import logging
from datetime import datetime
from typing import Any, TypeVar

from pepperpy.core.errors import ServiceError, StateError
from pepperpy.core.integration.protocols import (
    CommunicationProtocol,
    InMemoryProtocol,
    Message,
    MessageHandler,
    MessageType,
)
from pepperpy.core.integration.registry import (
    ServiceInfo,
    ServiceRegistry,
    ServiceStatus,
)
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.metrics import MetricsCollector

T = TypeVar("T")
U = TypeVar("U")


class Service(Lifecycle):
    """Base class for all services.

    This class provides core functionality for services including:
    - Lifecycle management (initialization, startup, shutdown)
    - Service registration and discovery
    - Inter-service communication
    - Metrics collection
    - Health checks
    """

    def __init__(
        self,
        name: str,
        registry: ServiceRegistry,
        protocol_class: type[CommunicationProtocol[Any, Any]] = InMemoryProtocol,
        metrics: MetricsCollector | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            name: Service name
            registry: Service registry instance
            protocol_class: Communication protocol class
            metrics: Optional metrics collector
            config: Optional service configuration
        """
        super().__init__()
        self.name = name
        self._registry = registry
        self._protocol_class = protocol_class
        self._metrics = metrics or MetricsCollector()
        self._config = config or {}
        self._logger = logging.getLogger(f"service.{name}")

        # Initialize metrics
        self._request_counter = self._metrics.counter(
            "service_requests_total", labels={"service": name}
        )
        self._error_counter = self._metrics.counter(
            "service_errors_total", labels={"service": name}
        )
        self._request_duration = self._metrics.histogram(
            "service_request_duration_seconds",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            labels={"service": name},
        )

    async def _initialize(self) -> None:
        """Initialize the service.

        This method:
        1. Validates configuration
        2. Sets up communication protocol
        3. Registers with service registry
        4. Starts health check task

        Raises:
            ConfigurationError: If configuration is invalid
            ServiceError: If initialization fails
        """
        try:
            # Validate configuration
            await self._validate_config()

            # Initialize protocol
            self._protocol = self._protocol_class(self.name, self._metrics)
            await self._protocol.initialize()

            # Register service
            await self._registry.register(
                ServiceInfo(
                    name=self.name,
                    status=ServiceStatus.RUNNING,
                    metadata=self._config,
                    last_heartbeat=datetime.now(),
                    instance=self,
                )
            )

            # Start health check
            self._health_check_task = asyncio.create_task(self._health_check())

            self._logger.info(f"Service {self.name} initialized")

        except Exception as e:
            self._error_counter.inc()
            raise ServiceError(f"Failed to initialize service: {e}") from e

    async def _cleanup(self) -> None:
        """Clean up the service.

        This method:
        1. Stops health check
        2. Unregisters from service registry
        3. Cleans up protocol
        """
        try:
            # Stop health check
            if hasattr(self, "_health_check_task"):
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # Unregister service
            await self._registry.unregister(self.name)

            # Clean up protocol
            if hasattr(self, "_protocol"):
                await self._protocol.stop()

            self._logger.info(f"Service {self.name} cleaned up")

        except Exception as e:
            self._error_counter.inc()
            self._logger.error(f"Error during cleanup: {e}", exc_info=True)
            raise

    async def _validate_config(self) -> None:
        """Validate service configuration.

        This method should be overridden by subclasses to perform
        service-specific configuration validation.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass

    async def _health_check(self) -> None:
        """Periodic health check task.

        This task:
        1. Updates service status
        2. Sends heartbeat to registry
        3. Collects metrics
        """
        while True:
            try:
                # Update status
                status = await self._get_health_status()
                await self._registry.update_status(self.name, status)

                # Send heartbeat
                await self._registry.heartbeat(self.name)

                # Collect metrics
                if status == ServiceStatus.ERROR:
                    self._error_counter.inc()

                await asyncio.sleep(30)  # Health check interval

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Health check failed: {e}", exc_info=True)
                self._error_counter.inc()
                await asyncio.sleep(5)  # Back off on error

    async def _get_health_status(self) -> ServiceStatus:
        """Get current service health status.

        This method should be overridden by subclasses to implement
        service-specific health checks.

        Returns:
            Current service status
        """
        return ServiceStatus.RUNNING if self.is_running() else ServiceStatus.ERROR

    async def send_message(
        self,
        target: str,
        payload: Any,
        message_type: MessageType = MessageType.REQUEST,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Message[Any] | None:
        """Send a message to another service.

        Args:
            target: Target service name
            payload: Message payload
            message_type: Type of message
            correlation_id: Optional correlation ID
            metadata: Optional message metadata

        Returns:
            Response message if request-response pattern

        Raises:
            StateError: If service is not running
            ServiceError: If sending fails
        """
        if not self.is_running():
            raise StateError("Service is not running")

        try:
            start_time = datetime.now()

            response = await self._protocol.send(
                target=target,
                payload=payload,
                message_type=message_type,
                correlation_id=correlation_id,
                metadata=metadata,
            )

            duration = (datetime.now() - start_time).total_seconds()
            self._request_duration.observe(duration)
            self._request_counter.inc()

            return response

        except Exception as e:
            self._error_counter.inc()
            raise ServiceError(f"Failed to send message: {e}") from e

    def register_handler(
        self, message_type: MessageType, handler: MessageHandler[Any, Any]
    ) -> None:
        """Register a message handler.

        Args:
            message_type: Type of messages to handle
            handler: Message handler

        Raises:
            StateError: If service is not running
        """
        if not self.is_running():
            raise StateError("Service is not running")

        self._protocol.register_handler(message_type, handler)
