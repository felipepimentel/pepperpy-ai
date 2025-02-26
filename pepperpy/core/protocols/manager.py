"""Protocol manager for the Pepperpy framework.

This module provides the protocol manager that handles protocol registration,
lifecycle management, and protocol discovery.
"""

from typing import Dict, List, Optional, Type, TypeVar

from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.monitoring.metrics import MetricsManager
from pepperpy.protocols import (
    BaseProtocol,
    ControlProtocol,
    EventProtocol,
    MessageProtocol,
    ProtocolConfig,
    StreamProtocol,
)

# Type variables
T = TypeVar("T", bound=BaseProtocol)


class ProtocolManager(Lifecycle):
    """Manager for protocol registration and lifecycle.

    This class manages protocol registration, initialization,
    and discovery for the framework.
    """

    def __init__(self) -> None:
        """Initialize protocol manager."""
        super().__init__()
        self._protocols: Dict[str, BaseProtocol] = {}
        self._metrics = MetricsManager.get_instance()
        self._logger = logger.getChild(self.__class__.__name__)
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize protocol manager.

        This method initializes the protocol manager and all registered
        protocols.

        Raises:
            RuntimeError: If initialization fails
        """
        try:
            # Initialize metrics
            self._operation_counter = await self._metrics.create_counter(
                name="protocol_manager_operations_total",
                description="Total protocol manager operations",
            )
            self._error_counter = await self._metrics.create_counter(
                name="protocol_manager_errors_total",
                description="Total protocol manager errors",
            )

            # Initialize protocols
            for protocol in self._protocols.values():
                await protocol.initialize()

            self._state = ComponentState.RUNNING
            self._logger.info("Protocol manager initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            self._logger.error(f"Failed to initialize protocol manager: {e}")
            raise RuntimeError(f"Failed to initialize protocol manager: {e}")

    async def cleanup(self) -> None:
        """Clean up protocol manager.

        This method cleans up the protocol manager and all registered
        protocols.

        Raises:
            RuntimeError: If cleanup fails
        """
        try:
            # Clean up protocols
            for protocol in self._protocols.values():
                await protocol.cleanup()

            self._protocols.clear()
            self._state = ComponentState.UNREGISTERED
            self._logger.info("Protocol manager cleaned up")
        except Exception as e:
            self._logger.error(f"Failed to clean up protocol manager: {e}")
            raise RuntimeError(f"Failed to clean up protocol manager: {e}")

    def register_protocol(
        self,
        protocol: BaseProtocol,
    ) -> None:
        """Register a protocol.

        Args:
            protocol: Protocol to register

        Raises:
            ValueError: If protocol is invalid
            RuntimeError: If registration fails
        """
        try:
            if not isinstance(protocol, BaseProtocol):
                raise ValueError("Invalid protocol type")

            protocol_id = str(protocol.id)
            if protocol_id in self._protocols:
                raise ValueError(f"Protocol {protocol_id} already registered")

            self._protocols[protocol_id] = protocol
            self._logger.info(f"Registered protocol {protocol_id}")
        except Exception as e:
            self._logger.error(f"Failed to register protocol: {e}")
            raise

    def unregister_protocol(
        self,
        protocol_id: str,
    ) -> None:
        """Unregister a protocol.

        Args:
            protocol_id: ID of protocol to unregister

        Raises:
            ValueError: If protocol not found
            RuntimeError: If unregistration fails
        """
        try:
            if protocol_id not in self._protocols:
                raise ValueError(f"Protocol {protocol_id} not found")

            del self._protocols[protocol_id]
            self._logger.info(f"Unregistered protocol {protocol_id}")
        except Exception as e:
            self._logger.error(f"Failed to unregister protocol: {e}")
            raise

    def get_protocol(
        self,
        protocol_id: str,
        protocol_type: Optional[Type[T]] = None,
    ) -> T:
        """Get a registered protocol.

        Args:
            protocol_id: Protocol ID
            protocol_type: Optional protocol type to validate

        Returns:
            Protocol instance

        Raises:
            ValueError: If protocol not found or type mismatch
        """
        try:
            if protocol_id not in self._protocols:
                raise ValueError(f"Protocol {protocol_id} not found")

            protocol = self._protocols[protocol_id]
            if protocol_type and not isinstance(protocol, protocol_type):
                raise ValueError(
                    f"Protocol {protocol_id} is not of type {protocol_type}"
                )

            return protocol  # type: ignore
        except Exception as e:
            self._logger.error(f"Failed to get protocol: {e}")
            raise

    def list_protocols(
        self,
        protocol_type: Optional[Type[BaseProtocol]] = None,
    ) -> List[BaseProtocol]:
        """List registered protocols.

        Args:
            protocol_type: Optional type to filter by

        Returns:
            List of registered protocols
        """
        try:
            if protocol_type:
                return [
                    p for p in self._protocols.values() if isinstance(p, protocol_type)
                ]
            return list(self._protocols.values())
        except Exception as e:
            self._logger.error(f"Failed to list protocols: {e}")
            raise

    def create_message_protocol(
        self,
        name: str,
        config: Optional[Dict[str, str]] = None,
    ) -> MessageProtocol:
        """Create a message protocol.

        Args:
            name: Protocol name
            config: Optional configuration

        Returns:
            MessageProtocol instance

        Raises:
            ValueError: If creation fails
        """
        try:
            protocol_config = ProtocolConfig(
                name=name,
                type="message",
                config=config or {},
            )
            protocol = MessageProtocol(config=protocol_config)
            self.register_protocol(protocol)
            return protocol
        except Exception as e:
            self._logger.error(f"Failed to create message protocol: {e}")
            raise

    def create_event_protocol(
        self,
        name: str,
        config: Optional[Dict[str, str]] = None,
    ) -> EventProtocol:
        """Create an event protocol.

        Args:
            name: Protocol name
            config: Optional configuration

        Returns:
            EventProtocol instance

        Raises:
            ValueError: If creation fails
        """
        try:
            protocol_config = ProtocolConfig(
                name=name,
                type="event",
                config=config or {},
            )
            protocol = EventProtocol(config=protocol_config)
            self.register_protocol(protocol)
            return protocol
        except Exception as e:
            self._logger.error(f"Failed to create event protocol: {e}")
            raise

    def create_stream_protocol(
        self,
        name: str,
        config: Optional[Dict[str, str]] = None,
    ) -> StreamProtocol:
        """Create a stream protocol.

        Args:
            name: Protocol name
            config: Optional configuration

        Returns:
            StreamProtocol instance

        Raises:
            ValueError: If creation fails
        """
        try:
            protocol_config = ProtocolConfig(
                name=name,
                type="stream",
                config=config or {},
            )
            protocol = StreamProtocol(config=protocol_config)
            self.register_protocol(protocol)
            return protocol
        except Exception as e:
            self._logger.error(f"Failed to create stream protocol: {e}")
            raise

    def create_control_protocol(
        self,
        name: str,
        config: Optional[Dict[str, str]] = None,
    ) -> ControlProtocol:
        """Create a control protocol.

        Args:
            name: Protocol name
            config: Optional configuration

        Returns:
            ControlProtocol instance

        Raises:
            ValueError: If creation fails
        """
        try:
            protocol_config = ProtocolConfig(
                name=name,
                type="control",
                config=config or {},
            )
            protocol = ControlProtocol(config=protocol_config)
            self.register_protocol(protocol)
            return protocol
        except Exception as e:
            self._logger.error(f"Failed to create control protocol: {e}")
            raise


# Export public API
__all__ = [
    "ProtocolManager",
]
