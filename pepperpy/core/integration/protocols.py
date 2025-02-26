"""Communication protocols for service-to-service interaction."""

from typing import Any, Dict, List, Optional, Protocol, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from datetime import datetime

from pepperpy.core.errors import CommunicationError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.metrics import MetricsCollector

T = TypeVar("T")
U = TypeVar("U")

class MessageType(Enum):
    """Message type enumeration."""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    HEARTBEAT = "heartbeat"
    ERROR = "error"

@dataclass
class Message(Generic[T]):
    """Message container for communication."""
    type: MessageType
    id: str
    source: str
    target: str
    payload: T
    timestamp: datetime
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MessageHandler(Protocol[T, U]):
    """Protocol for message handlers."""
    async def handle(self, message: Message[T]) -> Optional[Message[U]]:
        """Handle an incoming message."""
        ...

class CommunicationProtocol(Generic[T, U], Lifecycle):
    """Base class for communication protocols."""

    def __init__(
        self,
        service_name: str,
        metrics: Optional[MetricsCollector] = None
    ) -> None:
        """Initialize the communication protocol.
        
        Args:
            service_name: Name of the service using this protocol
            metrics: Optional metrics collector
        """
        super().__init__()
        self.service_name = service_name
        self._metrics = metrics or MetricsCollector()
        self._logger = logging.getLogger(__name__)
        self._handlers: Dict[MessageType, List[MessageHandler[T, U]]] = {
            t: [] for t in MessageType
        }
        self._pending_requests: Dict[str, asyncio.Future[Message[U]]] = {}

    async def send(
        self,
        target: str,
        payload: T,
        message_type: MessageType = MessageType.REQUEST,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Message[U]]:
        """Send a message to a target service.
        
        Args:
            target: Target service name
            payload: Message payload
            message_type: Type of message
            correlation_id: Optional correlation ID for request-response
            metadata: Optional message metadata
            
        Returns:
            Response message if request-response pattern
            
        Raises:
            CommunicationError: If sending fails
        """
        try:
            message = Message(
                type=message_type,
                id=f"{self.service_name}-{datetime.now().timestamp()}",
                source=self.service_name,
                target=target,
                payload=payload,
                timestamp=datetime.now(),
                correlation_id=correlation_id,
                metadata=metadata
            )
            
            self._metrics.counter(
                "messages_sent",
                labels={
                    "source": self.service_name,
                    "target": target,
                    "type": message_type.value
                }
            ).inc()
            
            if message_type == MessageType.REQUEST:
                return await self._send_request(message)
            else:
                await self._send_message(message)
                return None
            
        except Exception as e:
            self._metrics.counter(
                "message_errors",
                labels={
                    "source": self.service_name,
                    "target": target,
                    "type": "send_error"
                }
            ).inc()
            raise CommunicationError(f"Failed to send message: {e}")

    async def _send_request(self, message: Message[T]) -> Message[U]:
        """Send a request and wait for response.
        
        Args:
            message: Request message
            
        Returns:
            Response message
            
        Raises:
            CommunicationError: If request times out or fails
        """
        future: asyncio.Future[Message[U]] = asyncio.Future()
        self._pending_requests[message.id] = future
        
        try:
            await self._send_message(message)
            response = await asyncio.wait_for(future, timeout=30.0)
            return response
        except asyncio.TimeoutError:
            self._metrics.counter(
                "message_errors",
                labels={
                    "source": self.service_name,
                    "target": message.target,
                    "type": "timeout"
                }
            ).inc()
            raise CommunicationError(f"Request timed out: {message.id}")
        finally:
            self._pending_requests.pop(message.id, None)

    async def _send_message(self, message: Message[T]) -> None:
        """Send a message without waiting for response.
        
        Args:
            message: Message to send
            
        Raises:
            CommunicationError: If sending fails
        """
        raise NotImplementedError("Subclasses must implement _send_message")

    def register_handler(
        self,
        message_type: MessageType,
        handler: MessageHandler[T, U]
    ) -> None:
        """Register a message handler.
        
        Args:
            message_type: Type of messages to handle
            handler: Message handler
        """
        self._handlers[message_type].append(handler)
        self._logger.info(
            f"Registered handler for {message_type} messages: {handler.__class__.__name__}"
        )

    async def _handle_message(self, message: Message[T]) -> None:
        """Handle an incoming message.
        
        Args:
            message: Incoming message
        """
        try:
            self._metrics.counter(
                "messages_received",
                labels={
                    "source": message.source,
                    "target": self.service_name,
                    "type": message.type.value
                }
            ).inc()
            
            # Handle response messages
            if message.type == MessageType.RESPONSE and message.correlation_id:
                if message.correlation_id in self._pending_requests:
                    future = self._pending_requests[message.correlation_id]
                    if not future.done():
                        future.set_result(message)
                    return
            
            # Handle other messages
            handlers = self._handlers[message.type]
            for handler in handlers:
                try:
                    response = await handler.handle(message)
                    if response:
                        await self.send(
                            target=message.source,
                            payload=response.payload,
                            message_type=MessageType.RESPONSE,
                            correlation_id=message.id,
                            metadata=response.metadata
                        )
                except Exception as e:
                    self._logger.error(
                        f"Handler {handler.__class__.__name__} failed: {e}",
                        exc_info=True
                    )
                    self._metrics.counter(
                        "handler_errors",
                        labels={
                            "handler": handler.__class__.__name__,
                            "type": message.type.value
                        }
                    ).inc()
                    
        except Exception as e:
            self._logger.error(f"Failed to handle message: {e}", exc_info=True)
            self._metrics.counter(
                "message_errors",
                labels={
                    "source": message.source,
                    "target": self.service_name,
                    "type": "handle_error"
                }
            ).inc()

class InMemoryProtocol(CommunicationProtocol[T, U]):
    """In-memory communication protocol implementation."""

    _channels: Dict[str, asyncio.Queue[Message[Any]]] = {}
    _lock = asyncio.Lock()

    async def _initialize(self) -> None:
        """Initialize the protocol."""
        async with self._lock:
            if self.service_name not in self._channels:
                self._channels[self.service_name] = asyncio.Queue()
        
        # Start message processing
        self._process_task = asyncio.create_task(self._process_messages())
        self._logger.info(f"Initialized in-memory protocol for {self.service_name}")

    async def _cleanup(self) -> None:
        """Clean up the protocol."""
        if hasattr(self, "_process_task"):
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        
        async with self._lock:
            self._channels.pop(self.service_name, None)
        
        self._logger.info(f"Cleaned up in-memory protocol for {self.service_name}")

    async def _send_message(self, message: Message[T]) -> None:
        """Send a message to target service queue.
        
        Args:
            message: Message to send
            
        Raises:
            CommunicationError: If target service not found
        """
        async with self._lock:
            if message.target not in self._channels:
                raise CommunicationError(f"Target service not found: {message.target}")
            
            await self._channels[message.target].put(message)

    async def _process_messages(self) -> None:
        """Process incoming messages from the service queue."""
        while True:
            try:
                message = await self._channels[self.service_name].get()
                asyncio.create_task(self._handle_message(message))
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error processing message: {e}", exc_info=True)
                await asyncio.sleep(1)  # Back off on error