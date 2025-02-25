"""Example service implementation demonstrating core integration features."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.integration.protocols import Message, MessageHandler, MessageType
from pepperpy.core.integration.registry import ServiceRegistry, ServiceStatus
from pepperpy.core.service import Service


@dataclass
class EchoRequest:
    """Echo request message."""

    message: str


@dataclass
class EchoResponse:
    """Echo response message."""

    message: str
    timestamp: str


class EchoHandler(MessageHandler[EchoRequest, EchoResponse]):
    """Handler for echo requests."""

    def __init__(self, service: "EchoService") -> None:
        """Initialize the handler.

        Args:
            service: Parent service instance
        """
        self._service = service
        self._logger = logging.getLogger(__name__)

    async def handle(
        self, message: Message[EchoRequest]
    ) -> Message[EchoResponse] | None:
        """Handle echo request.

        Args:
            message: Request message

        Returns:
            Response message with echoed content
        """
        try:
            self._logger.info(f"Received echo request: {message.payload.message}")

            # Process the request
            response_payload = EchoResponse(
                message=f"Echo: {message.payload.message}",
                timestamp=str(message.timestamp),
            )

            # Create response message
            return Message(
                type=MessageType.RESPONSE,
                id=f"{self._service.name}-response-{message.id}",
                source=self._service.name,
                target=message.source,
                payload=response_payload,
                timestamp=message.timestamp,
                correlation_id=message.id,
                metadata=message.metadata,
            )

        except Exception as e:
            self._logger.error(f"Error handling echo request: {e}", exc_info=True)
            return None


class EchoService(Service):
    """Example service that echoes received messages.

    This service demonstrates:
    - Service configuration and validation
    - Message handling
    - Health checks
    - Metrics collection
    """

    def __init__(
        self, name: str, registry: ServiceRegistry, config: dict[str, Any] | None = None
    ) -> None:
        """Initialize the echo service.

        Args:
            name: Service name
            registry: Service registry instance
            config: Optional service configuration
        """
        super().__init__(name, registry, config=config)

        # Register message handlers
        self._echo_handler = EchoHandler(self)

    async def _validate_config(self) -> None:
        """Validate service configuration.

        Required config:
        - max_message_length: Maximum allowed message length

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if "max_message_length" not in self._config:
            raise ConfigurationError("max_message_length not specified")

        max_length = self._config["max_message_length"]
        if not isinstance(max_length, int) or max_length <= 0:
            raise ConfigurationError("max_message_length must be a positive integer")

    async def _initialize(self) -> None:
        """Initialize the service.

        This method:
        1. Calls parent initialization
        2. Registers message handlers
        """
        await super()._initialize()

        # Register handlers
        self.register_handler(MessageType.REQUEST, self._echo_handler)

        self._logger.info(
            f"Echo service initialized with max_message_length={self._config['max_message_length']}"
        )

    async def _get_health_status(self) -> ServiceStatus:
        """Get current service health status.

        This implementation considers the service healthy if:
        1. It is running
        2. Message handlers are registered
        3. Error count is below threshold

        Returns:
            Current service status
        """
        if not self.is_running():
            return ServiceStatus.ERROR

        if not hasattr(self, "_echo_handler"):
            return ServiceStatus.ERROR

        error_count = self._error_counter.value
        if error_count > 100:  # Example threshold
            return ServiceStatus.ERROR

        return ServiceStatus.RUNNING


async def main() -> None:
    """Example usage of the echo service."""
    # Create service registry
    registry = ServiceRegistry()
    await registry.initialize()

    try:
        # Create and start echo service
        echo_service = EchoService(
            name="echo", registry=registry, config={"max_message_length": 1000}
        )
        await echo_service.initialize()

        # Create test client
        client = Service("client", registry)
        await client.initialize()

        try:
            # Send test message
            request = EchoRequest(message="Hello, Echo Service!")
            response = await client.send_message(
                target="echo", payload=request, message_type=MessageType.REQUEST
            )

            if response:
                print(f"Received response: {response.payload.message}")

        finally:
            await client.stop()

    finally:
        await echo_service.stop()
        await registry.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
