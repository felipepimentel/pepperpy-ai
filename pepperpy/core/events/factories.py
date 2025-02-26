"""Event and message factories module.

This module provides factories for creating events and messages.
"""

import logging
from typing import Any, Dict, Optional

from pepperpy.events.types import (
    Event,
    EventType,
    Notification,
    Request,
    Response,
)

# Configure logging
logger = logging.getLogger(__name__)


class EventFactory:
    """Event factory implementation.

    This class provides methods for creating events.
    """

    @staticmethod
    def create_event(
        event_type: EventType,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> Event:
        """Create event.

        Args:
            event_type: Event type
            source: Event source
            metadata: Event metadata
            error: Event error

        Returns:
            Event: Created event
        """
        return Event(
            type=event_type,
            source=source,
            metadata=metadata or {},
            error=error,
        )

    @staticmethod
    def create_system_event(
        source: str,
        action: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> Event:
        """Create system event.

        Args:
            source: Event source
            action: System action
            status: Action status
            metadata: Additional metadata
            error: Event error

        Returns:
            Event: Created event
        """
        event_metadata = {
            "action": action,
            "status": status,
            **(metadata or {}),
        }
        return EventFactory.create_event(
            event_type=EventType.SYSTEM,
            source=source,
            metadata=event_metadata,
            error=error,
        )

    @staticmethod
    def create_component_event(
        source: str,
        component_type: str,
        action: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> Event:
        """Create component event.

        Args:
            source: Event source
            component_type: Component type
            action: Component action
            status: Action status
            metadata: Additional metadata
            error: Event error

        Returns:
            Event: Created event
        """
        event_metadata = {
            "component_type": component_type,
            "action": action,
            "status": status,
            **(metadata or {}),
        }
        return EventFactory.create_event(
            event_type=EventType.COMPONENT,
            source=source,
            metadata=event_metadata,
            error=error,
        )

    @staticmethod
    def create_resource_event(
        source: str,
        resource_type: str,
        action: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> Event:
        """Create resource event.

        Args:
            source: Event source
            resource_type: Resource type
            action: Resource action
            status: Action status
            metadata: Additional metadata
            error: Event error

        Returns:
            Event: Created event
        """
        event_metadata = {
            "resource_type": resource_type,
            "action": action,
            "status": status,
            **(metadata or {}),
        }
        return EventFactory.create_event(
            event_type=EventType.RESOURCE,
            source=source,
            metadata=event_metadata,
            error=error,
        )

    @staticmethod
    def create_error_event(
        source: str,
        error: Exception,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """Create error event.

        Args:
            source: Event source
            error: Error exception
            metadata: Additional metadata

        Returns:
            Event: Created event
        """
        event_metadata = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **(metadata or {}),
        }
        return EventFactory.create_event(
            event_type=EventType.ERROR,
            source=source,
            metadata=event_metadata,
            error=error,
        )


class MessageFactory:
    """Message factory implementation.

    This class provides methods for creating messages.
    """

    @staticmethod
    def create_request(
        sender: str,
        receiver: str,
        request_type: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Request:
        """Create request message.

        Args:
            sender: Message sender
            receiver: Message receiver
            request_type: Request type
            data: Request data
            metadata: Additional metadata

        Returns:
            Request: Created request
        """
        message_metadata = {
            "type": request_type,
            "data": data or {},
            **(metadata or {}),
        }
        return Request(
            sender=sender,
            receiver=receiver,
            action=request_type,
            parameters=data or {},
            metadata=message_metadata,
        )

    @staticmethod
    def create_response(
        sender: str,
        receiver: str,
        request_id: str,
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """Create response message.

        Args:
            sender: Message sender
            receiver: Message receiver
            request_id: Original request ID
            result: Response result
            metadata: Additional metadata

        Returns:
            Response: Created response
        """
        message_metadata = {
            "request_id": request_id,
            **(metadata or {}),
        }
        return Response(
            sender=sender,
            receiver=receiver,
            request_id=request_id,
            result=result,
            metadata=message_metadata,
        )

    @staticmethod
    def create_notification(
        sender: str,
        notification_type: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create notification message.

        Args:
            sender: Message sender
            notification_type: Notification type
            title: Notification title
            body: Notification body
            data: Notification data
            metadata: Additional metadata

        Returns:
            Notification: Created notification
        """
        message_metadata = {
            "type": notification_type,
            "data": data or {},
            **(metadata or {}),
        }
        return Notification(
            sender=sender,
            receiver="*",  # Broadcast to all
            title=title,
            body=body,
            metadata=message_metadata,
        )
