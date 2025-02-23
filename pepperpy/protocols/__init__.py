"""Protocol system for the Pepperpy framework.

This module provides a unified protocol system for all types of communication
within the framework. It includes:

- Message protocols for structured communication
- Event protocols for pub/sub patterns
- Stream protocols for continuous data
- Control protocols for system management

The protocol system ensures consistent interfaces, serialization,
validation, and error handling across all communication types.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Set,
    TypeVar,
    Union,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from pepperpy.monitoring.metrics import Counter, Histogram, MetricsManager

# Type variables for generic protocols
T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)


# Protocol configuration
class ProtocolConfig(BaseModel):
    """Configuration for protocols.

    Attributes:
        id: Unique identifier
        name: Protocol name
        type: Protocol type
        version: Protocol version
        config: Additional configuration
    """

    id: UUID = Field(default_factory=uuid4)
    name: str
    type: str
    version: str = "1.0.0"
    config: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure config is immutable."""
        return dict(v)


# Protocol types
class ProtocolType(str, Enum):
    """Types of protocols."""

    MESSAGE = "message"
    EVENT = "event"
    STREAM = "stream"
    CONTROL = "control"


# Base protocol interface
class BaseProtocol(ABC):
    """Base class for all protocols.

    This class defines the core interface that all protocols must implement,
    including lifecycle management, validation, and metrics.
    """

    def __init__(self, config: ProtocolConfig) -> None:
        """Initialize protocol.

        Args:
            config: Protocol configuration
        """
        self.config = config
        self._metrics = MetricsManager.get_instance()
        self._initialized = False

    @property
    def id(self) -> UUID:
        """Get protocol ID."""
        return self.config.id

    @property
    def name(self) -> str:
        """Get protocol name."""
        return self.config.name

    @property
    def type(self) -> str:
        """Get protocol type."""
        return self.config.type

    @property
    def version(self) -> str:
        """Get protocol version."""
        return self.config.version

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize protocol.

        This method should be called before using the protocol.
        It should set up any necessary resources and validate configuration.

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If initialization fails
        """
        if self._initialized:
            return

        # Initialize metrics
        self._operation_counter = await self._metrics.create_counter(
            name=f"{self.name}_operations_total",
            description=f"Total operations for {self.name} protocol",
            labels={"type": self.type, "version": self.version},
        )

        self._error_counter = await self._metrics.create_counter(
            name=f"{self.name}_errors_total",
            description=f"Total errors for {self.name} protocol",
            labels={"type": self.type, "version": self.version},
        )

        self._latency_histogram = await self._metrics.create_histogram(
            name=f"{self.name}_operation_latency_seconds",
            description=f"Operation latency for {self.name} protocol",
            labels={"type": self.type, "version": self.version},
        )

        self._initialized = True

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up protocol resources.

        This method should be called when the protocol is no longer needed.
        It should clean up any resources and perform necessary shutdown tasks.

        Raises:
            RuntimeError: If cleanup fails
        """
        self._initialized = False

    @abstractmethod
    async def validate(self, data: Any) -> bool:
        """Validate protocol data.

        Args:
            data: Data to validate

        Returns:
            bool: True if data is valid

        Raises:
            ValueError: If data is invalid
        """
        pass


# Message protocol
class MessageProtocol(BaseProtocol):
    """Protocol for message-based communication.

    This protocol handles structured messages between components,
    with support for different message types and validation.
    """

    def __init__(self, config: ProtocolConfig) -> None:
        """Initialize message protocol.

        Args:
            config: Protocol configuration
        """
        super().__init__(config)

    async def initialize(self) -> None:
        """Initialize message protocol."""
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up message protocol."""
        await super().cleanup()

    async def validate(self, data: Any) -> bool:
        """Validate message data.

        Args:
            data: Message data to validate

        Returns:
            bool: True if message is valid

        Raises:
            ValueError: If message is invalid
        """
        if not isinstance(data, (str, dict, BaseModel)):
            raise ValueError("Invalid message format")
        return True

    async def create_message(
        self,
        content: Any,
        type: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Message":
        """Create a new message.

        Args:
            content: Message content
            type: Message type
            metadata: Optional message metadata

        Returns:
            Message: Created message

        Raises:
            ValueError: If message creation fails
        """
        if not self._initialized:
            raise RuntimeError("Protocol not initialized")

        start_time = datetime.utcnow()
        try:
            await self.validate(content)
            message = Message(
                content=content,
                type=type,
                metadata=metadata or {},
            )
            await self._operation_counter.inc()
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._latency_histogram.observe(duration)
            return message
        except Exception as e:
            await self._error_counter.inc()
            raise ValueError(f"Failed to create message: {e}")


# Event protocol
class EventProtocol(BaseProtocol):
    """Protocol for event-based communication.

    This protocol handles event publishing and subscription,
    with support for event filtering and middleware.
    """

    def __init__(self, config: ProtocolConfig) -> None:
        """Initialize event protocol.

        Args:
            config: Protocol configuration
        """
        super().__init__(config)
        self._handlers: Dict[str, Set[Any]] = {}
        self._middleware: List[Any] = []

    async def initialize(self) -> None:
        """Initialize event protocol."""
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up event protocol."""
        self._handlers.clear()
        self._middleware.clear()
        await super().cleanup()

    async def validate(self, data: Any) -> bool:
        """Validate event data.

        Args:
            data: Event data to validate

        Returns:
            bool: True if event is valid

        Raises:
            ValueError: If event is invalid
        """
        if not isinstance(data, (dict, BaseModel)):
            raise ValueError("Invalid event format")
        return True

    async def publish(
        self,
        event_type: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish an event.

        Args:
            event_type: Type of event
            data: Event data
            metadata: Optional event metadata

        Raises:
            ValueError: If event publication fails
        """
        if not self._initialized:
            raise RuntimeError("Protocol not initialized")

        start_time = datetime.utcnow()
        try:
            await self.validate(data)
            event = Event(
                type=event_type,
                data=data,
                metadata=metadata or {},
            )

            # Process through middleware
            current_event = event
            for middleware in self._middleware:
                current_event = await middleware.process(current_event)

            # Dispatch to handlers
            if event_type in self._handlers:
                for handler in self._handlers[event_type]:
                    await handler(current_event)

            await self._operation_counter.inc()
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._latency_histogram.observe(duration)
        except Exception as e:
            await self._error_counter.inc()
            raise ValueError(f"Failed to publish event: {e}")


# Stream protocol
class StreamProtocol(BaseProtocol):
    """Protocol for stream-based communication.

    This protocol handles continuous data streams between components,
    with support for different stream modes and buffering.
    """

    def __init__(self, config: ProtocolConfig) -> None:
        """Initialize stream protocol.

        Args:
            config: Protocol configuration
        """
        super().__init__(config)

    async def initialize(self) -> None:
        """Initialize stream protocol."""
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up stream protocol."""
        await super().cleanup()

    async def validate(self, data: Any) -> bool:
        """Validate stream data.

        Args:
            data: Stream data to validate

        Returns:
            bool: True if stream data is valid

        Raises:
            ValueError: If stream data is invalid
        """
        return True

    async def create_stream(
        self,
        name: str,
        mode: str = "text",
        buffer_size: int = 1024,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Any, None]:
        """Create a new stream.

        Args:
            name: Stream name
            mode: Stream mode (text/binary)
            buffer_size: Stream buffer size
            metadata: Optional stream metadata

        Returns:
            AsyncGenerator: Stream generator

        Raises:
            ValueError: If stream creation fails
        """
        if not self._initialized:
            raise RuntimeError("Protocol not initialized")

        start_time = datetime.utcnow()
        try:
            # Stream implementation
            async def stream_generator() -> AsyncGenerator[Any, None]:
                try:
                    while True:
                        # Stream logic here
                        yield None
                finally:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    await self._latency_histogram.observe(duration)

            await self._operation_counter.inc()
            return stream_generator()
        except Exception as e:
            await self._error_counter.inc()
            raise ValueError(f"Failed to create stream: {e}")


# Control protocol
class ControlProtocol(BaseProtocol):
    """Protocol for control operations.

    This protocol handles system control and management operations,
    with support for command validation and response handling.
    """

    def __init__(self, config: ProtocolConfig) -> None:
        """Initialize control protocol.

        Args:
            config: Protocol configuration
        """
        super().__init__(config)

    async def initialize(self) -> None:
        """Initialize control protocol."""
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up control protocol."""
        await super().cleanup()

    async def validate(self, data: Any) -> bool:
        """Validate control data.

        Args:
            data: Control data to validate

        Returns:
            bool: True if control data is valid

        Raises:
            ValueError: If control data is invalid
        """
        if not isinstance(data, (str, dict)):
            raise ValueError("Invalid control format")
        return True

    async def create_control(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Control":
        """Create a control command.

        Args:
            command: Control command
            parameters: Command parameters
            metadata: Optional command metadata

        Returns:
            Control: Created control command

        Raises:
            ValueError: If control creation fails
        """
        if not self._initialized:
            raise RuntimeError("Protocol not initialized")

        start_time = datetime.utcnow()
        try:
            await self.validate(parameters or {})
            control = Control(
                command=command,
                parameters=parameters or {},
                metadata=metadata or {},
            )
            await self._operation_counter.inc()
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._latency_histogram.observe(duration)
            return control
        except Exception as e:
            await self._error_counter.inc()
            raise ValueError(f"Failed to create control: {e}")


# Message type
class Message(BaseModel):
    """A message that can be exchanged between components.

    Attributes:
        id: Message ID
        content: Message content
        type: Message type
        metadata: Message metadata
    """

    id: UUID = Field(default_factory=uuid4)
    content: Any
    type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure metadata is immutable."""
        return dict(v)


# Event type
class Event(BaseModel):
    """An event that can be published and subscribed to.

    Attributes:
        id: Event ID
        type: Event type
        data: Event data
        metadata: Event metadata
        timestamp: Event timestamp
    """

    id: UUID = Field(default_factory=uuid4)
    type: str
    data: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure metadata is immutable."""
        return dict(v)


# Control type
class Control(BaseModel):
    """A control command for system management.

    Attributes:
        id: Control ID
        command: Control command
        parameters: Command parameters
        metadata: Command metadata
        timestamp: Command timestamp
    """

    id: UUID = Field(default_factory=uuid4)
    command: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("metadata", "parameters")
    @classmethod
    def validate_dicts(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure dictionaries are immutable."""
        return dict(v)


# Export public API
__all__ = [
    "ProtocolConfig",
    "ProtocolType",
    "BaseProtocol",
    "MessageProtocol",
    "EventProtocol",
    "StreamProtocol",
    "ControlProtocol",
    "Message",
    "Event",
    "Control",
    "Counter",
    "Histogram",
]
