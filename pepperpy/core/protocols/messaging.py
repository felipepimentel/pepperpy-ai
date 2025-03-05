"""Messaging protocols for PepperPy.

This module defines protocols for message handling and communication
between components in the PepperPy framework.
"""

from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

T = TypeVar("T")  # Message type
R = TypeVar("R")  # Response type


class Message(Protocol):
    """Protocol for messages in the system."""

    @property
    def id(self) -> str:
        """Get message ID.

        Returns:
            Message ID
        """
        ...

    @property
    def type(self) -> str:
        """Get message type.

        Returns:
            Message type
        """
        ...

    @property
    def payload(self) -> Dict[str, Any]:
        """Get message payload.

        Returns:
            Message payload
        """
        ...


class MessageHandler(Generic[T, R], Protocol):
    """Protocol for message handlers.

    This protocol defines the interface for components that handle messages
    in the system.
    """

    async def handle(self, message: T) -> R:
        """Handle a message.

        Args:
            message: Message to handle

        Returns:
            Response to the message
        """
        ...


class MessageBus(ABC):
    """Abstract base class for message buses.

    A message bus is responsible for routing messages between components
    in the system.
    """

    @abstractmethod
    async def publish(self, topic: str, message: Any) -> None:
        """Publish a message to a topic.

        Args:
            topic: Topic to publish to
            message: Message to publish
        """
        pass

    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable[[Any], Any]) -> None:
        """Subscribe to a topic.

        Args:
            topic: Topic to subscribe to
            handler: Handler function for messages on the topic
        """
        pass

    @abstractmethod
    async def unsubscribe(self, topic: str, handler: Callable[[Any], Any]) -> None:
        """Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from
            handler: Handler function to unsubscribe
        """
        pass


class EventEmitter(ABC):
    """Abstract base class for event emitters.

    An event emitter is responsible for emitting events to registered
    listeners.
    """

    @abstractmethod
    def on(self, event: str, listener: Callable[..., Any]) -> None:
        """Register an event listener.

        Args:
            event: Event name
            listener: Listener function
        """
        pass

    @abstractmethod
    def off(self, event: str, listener: Callable[..., Any]) -> None:
        """Unregister an event listener.

        Args:
            event: Event name
            listener: Listener function
        """
        pass

    @abstractmethod
    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event.

        Args:
            event: Event name
            *args: Positional arguments for the event
            **kwargs: Keyword arguments for the event
        """
        pass


class MessageQueue(ABC):
    """Abstract base class for message queues.

    A message queue is responsible for storing and retrieving messages
    in a first-in, first-out (FIFO) order.
    """

    @abstractmethod
    async def enqueue(self, message: Any) -> None:
        """Enqueue a message.

        Args:
            message: Message to enqueue
        """
        pass

    @abstractmethod
    async def dequeue(self) -> Optional[Any]:
        """Dequeue a message.

        Returns:
            The next message in the queue, or None if the queue is empty
        """
        pass

    @abstractmethod
    async def peek(self) -> Optional[Any]:
        """Peek at the next message in the queue.

        Returns:
            The next message in the queue without removing it,
            or None if the queue is empty
        """
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        """Check if the queue is empty.

        Returns:
            True if the queue is empty, False otherwise
        """
        pass

    @abstractmethod
    def size(self) -> int:
        """Get the size of the queue.

        Returns:
            Number of messages in the queue
        """
        pass
