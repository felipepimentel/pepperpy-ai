"""
Base classes and interfaces for the communication module.

This module defines the core abstractions for communication providers and protocols,
enabling consistent interactions across different communication mechanisms.
"""

import abc
import enum
from typing import Any, AsyncGenerator, Dict, runtime_checkable, Protocol

from pepperpy.core.logging import get_logger
from pepperpy.core.errors import PepperpyError

logger = get_logger(__name__)


class CommunicationError(PepperpyError):
    """Base exception for communication-related errors."""

    pass


class MessagePartType(enum.Enum):
    """Enum for different types of message parts."""

    TEXT = "text"
    DATA = "data"
    FILE = "file"


class MessagePart:
    """Base class for message parts."""

    def __init__(self, type_: MessagePartType):
        self.type = type_


class TextPart(MessagePart):
    """A text part of a message."""

    def __init__(self, text: str, role: str | None = None):
        super().__init__(MessagePartType.TEXT)
        self.text = text
        self.role = role

    def __repr__(self) -> str:
        return (
            f"TextPart(text='{self.text[:20]}...', role={self.role})"
            if len(self.text) > 20
            else f"TextPart(text='{self.text}', role={self.role})"
        )


class DataPart(MessagePart):
    """A structured data part of a message."""

    def __init__(self, data: dict[str, Any], format_: str | None = None):
        super().__init__(MessagePartType.DATA)
        self.data = data
        self.format = format_

    def __repr__(self) -> str:
        return f"DataPart(data={self.data}, format={self.format})"


class FilePart(MessagePart):
    """A file part of a message."""

    def __init__(
        self, path: str, mime_type: str | None = None, content: bytes | None = None
    ):
        super().__init__(MessagePartType.FILE)
        self.path = path
        self.mime_type = mime_type
        self.content = content

    def __repr__(self) -> str:
        return f"FilePart(path='{self.path}', mime_type={self.mime_type})"


class Message:
    """Representation of a communication message."""

    def __init__(
        self,
        parts: list[MessagePart] | None = None,
        task_id: str | None = None,
        sender: str | None = None,
        receiver: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.parts = parts or []
        self.task_id = task_id
        self.sender = sender
        self.receiver = receiver
        self.metadata = metadata or {}

    def add_part(self, part: MessagePart) -> None:
        """Add a part to the message."""
        self.parts.append(part)

    def get_text_parts(self) -> list[TextPart]:
        """Get all text parts from the message."""
        return [part for part in self.parts if isinstance(part, TextPart)]

    def get_data_parts(self) -> list[DataPart]:
        """Get all data parts from the message."""
        return [part for part in self.parts if isinstance(part, DataPart)]

    def get_file_parts(self) -> list[FilePart]:
        """Get all file parts from the message."""
        return [part for part in self.parts if isinstance(part, FilePart)]

    def __repr__(self) -> str:
        return f"Message(task_id={self.task_id}, parts={len(self.parts)}, sender={self.sender}, receiver={self.receiver})"


class CommunicationProtocol(enum.Enum):
    """Enum for different communication protocols."""

    A2A = "a2a"
    MCP = "mcp"
    # Add more protocols as needed


@runtime_checkable
class CommunicationProvider(Protocol):
    """Interface for communication providers."""
    
    @property
    def protocol_type(self) -> CommunicationProtocol:
        """Get the protocol type.
        
        Returns:
            Communication protocol type
        """
        ...
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        ...
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        ...
    
    async def send_message(self, message: Message) -> str:
        """
        Send a message using this communication provider.

        Args:
            message: The message to send

        Returns:
            The task ID of the sent message

        Raises:
            CommunicationError: If sending the message fails
        """
        ...

    async def receive_message(self, task_id: str) -> Message:
        """
        Receive a message with the given task ID.

        Args:
            task_id: The task ID of the message to receive

        Returns:
            The received message

        Raises:
            CommunicationError: If receiving the message fails
        """
        ...

    async def stream_messages(
        self, filter_criteria: dict[str, Any] | None = None
    ) -> AsyncGenerator[Message, None]:
        """
        Stream messages matching the given filter criteria.

        Args:
            filter_criteria: Optional criteria to filter messages by

        Yields:
            Messages matching the filter criteria

        Raises:
            CommunicationError: If streaming messages fails
        """
        ...


class BaseCommunicationProvider(abc.ABC):
    """Base implementation of a communication provider with common utility methods."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize provider with configuration.
        
        Args:
            **kwargs: Configuration options
        """
        self.config = kwargs
        self._initialized = False
        self.logger = get_logger(self.__class__.__module__)

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self._initialized:
            return

        await self._initialize_resources()
        self._initialized = True
        self.logger.debug(f"Initialized {self.__class__.__name__}")

    async def cleanup(self) -> None:
        """Clean up any resources used by the provider."""
        if not self._initialized:
            return
            
        await self._cleanup_resources()
        self._initialized = False
        self.logger.debug(f"Cleaned up {self.__class__.__name__}")
        
    async def _initialize_resources(self) -> None:
        """Initialize any resources needed by the provider.
        
        This method should be overridden by subclasses.
        """
        pass
        
    async def _cleanup_resources(self) -> None:
        """Clean up any resources used by the provider.
        
        This method should be overridden by subclasses.
        """
        pass
        
    async def __aenter__(self) -> "BaseCommunicationProvider":
        """Enter async context manager."""
        await self.initialize()
        return self
        
    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.cleanup()


async def create_provider(
    protocol: str | CommunicationProtocol, 
    provider_type: str = "default",
    **kwargs: Any
) -> CommunicationProvider:
    """
    Create a communication provider for the specified protocol.

    Args:
        protocol: The communication protocol to use
        provider_type: The specific provider implementation to use
        **kwargs: Additional configuration arguments for the provider

    Returns:
        A communication provider instance

    Raises:
        CommunicationError: If creating the provider fails
    """
    from pepperpy.plugin.base import create_provider_instance
    
    if isinstance(protocol, CommunicationProtocol):
        protocol_str = protocol.value
    else:
        protocol_str = protocol
    
    try:
        # Use the plugin system to create the provider
        provider = await create_provider_instance(
            domain="communication",
            provider_type=f"{protocol_str}_{provider_type}",
            **kwargs
        )
        
        # Verify it implements the communication interface
        if not isinstance(provider, CommunicationProvider):
            raise CommunicationError(
                f"Provider {protocol_str}_{provider_type} does not implement CommunicationProvider interface"
            )
            
        return provider
    except Exception as e:
        raise CommunicationError(f"Failed to create communication provider: {e}") from e
