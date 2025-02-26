"""Message processors base module.

This module provides base implementations for message processors.
"""

import logging
from typing import Any, Dict, Optional, Set, Type

from pepperpy.core.base import ComponentBase
from pepperpy.core.metrics import Counter, Histogram
from pepperpy.events.types import (
    Message,
    Request,
    Response,
    Notification,
)

# Configure logging
logger = logging.getLogger(__name__)


class BaseMessageProcessor(ComponentBase):
    """Base message processor implementation.

    This class provides a base implementation for message processors.
    """

    def __init__(self, message_types: Set[Type[Message]]) -> None:
        """Initialize processor.

        Args:
            message_types: Message types to process
        """
        super().__init__()
        self.message_types = message_types

        # Initialize metrics
        self._messages_processed = Counter(
            "messages_processed_total", "Total number of messages processed"
        )
        self._message_errors = Counter(
            "message_errors_total", "Total number of message processing errors"
        )
        self._message_duration = Histogram(
            "message_duration_seconds", "Message processing duration in seconds"
        )

    def can_process(self, message: Message) -> bool:
        """Check if processor can process message.

        Args:
            message: Message to check

        Returns:
            bool: True if processor can process message
        """
        return type(message) in self.message_types

    async def process(self, message: Message) -> Optional[Message]:
        """Process message.

        Args:
            message: Message to process

        Returns:
            Optional[Message]: Response message if any
        """
        self._messages_processed.inc()
        try:
            return await self._process_message(message)
        except Exception as e:
            self._message_errors.inc()
            logger.error(
                f"Failed to process message: {e}",
                extra={
                    "message_type": type(message).__name__,
                    "metadata": message.metadata,
                },
                exc_info=True,
            )
            raise

    async def _process_message(self, message: Message) -> Optional[Message]:
        """Process message implementation.

        This method must be implemented by subclasses.

        Args:
            message: Message to process

        Returns:
            Optional[Message]: Response message if any
        """
        raise NotImplementedError("Message processing not implemented")


class RequestProcessor(BaseMessageProcessor):
    """Request processor implementation.

    This class processes request messages.
    """

    def __init__(self) -> None:
        """Initialize processor."""
        super().__init__({Request})

    async def _process_message(self, message: Message) -> Optional[Message]:
        """Process request message.

        Args:
            message: Message to process

        Returns:
            Optional[Message]: Response message if any
        """
        if not isinstance(message, Request):
            return None

        request_type = message.metadata.get("type", "")
        request_data = message.metadata.get("data", {})

        logger.debug(
            f"Processing request: {request_type}",
            extra={
                "metadata": message.metadata,
            },
        )

        # Process request based on type
        if request_type == "query":
            return await self._handle_query(message, request_data)
        elif request_type == "command":
            return await self._handle_command(message, request_data)
        else:
            logger.warning(
                f"Unknown request type: {request_type}",
                extra={"metadata": message.metadata},
            )
            return None

    async def _handle_query(self, request: Request, data: Dict[str, Any]) -> Response:
        """Handle query request.

        Args:
            request: Request message
            data: Request data

        Returns:
            Response: Response message
        """
        # TODO: Implement query handling
        return Response(
            sender=self.__class__.__name__,
            receiver=request.sender,
            request_id=request.metadata.get("request_id", ""),
            result={
                "type": "query_result",
                "data": {},
            },
        )

    async def _handle_command(self, request: Request, data: Dict[str, Any]) -> Response:
        """Handle command request.

        Args:
            request: Request message
            data: Request data

        Returns:
            Response: Response message
        """
        # TODO: Implement command handling
        return Response(
            sender=self.__class__.__name__,
            receiver=request.sender,
            request_id=request.metadata.get("request_id", ""),
            result={
                "type": "command_result",
                "data": {},
            },
        )


class NotificationProcessor(BaseMessageProcessor):
    """Notification processor implementation.

    This class processes notification messages.
    """

    def __init__(self) -> None:
        """Initialize processor."""
        super().__init__({Notification})

    async def _process_message(self, message: Message) -> Optional[Message]:
        """Process notification message.

        Args:
            message: Message to process

        Returns:
            Optional[Message]: Response message if any
        """
        if not isinstance(message, Notification):
            return None

        notification_type = message.metadata.get("type", "")
        notification_data = message.metadata.get("data", {})

        logger.debug(
            f"Processing notification: {notification_type}",
            extra={
                "metadata": message.metadata,
            },
        )

        # Process notification based on type
        if notification_type == "status":
            await self._handle_status(notification_data)
        elif notification_type == "alert":
            await self._handle_alert(notification_data)
        else:
            logger.warning(
                f"Unknown notification type: {notification_type}",
                extra={"metadata": message.metadata},
            )

        return None

    async def _handle_status(self, data: Dict[str, Any]) -> None:
        """Handle status notification.

        Args:
            data: Notification data
        """
        status = data.get("status", "unknown")
        component = data.get("component", "unknown")

        logger.info(
            f"Status update: {component} is {status}",
            extra={"data": data},
        )

    async def _handle_alert(self, data: Dict[str, Any]) -> None:
        """Handle alert notification.

        Args:
            data: Notification data
        """
        level = data.get("level", "info")
        message = data.get("message", "")

        logger.log(
            getattr(logging, level.upper(), logging.INFO),
            f"Alert: {message}",
            extra={"data": data},
        )
