"""Event handlers for the Pepperpy framework.

This module provides event handlers for different components.
"""

from abc import ABC, abstractmethod
from typing import Any

from pepperpy.core.events.types import EventType


class EventHandler(ABC):
    """Base class for event handlers."""

    @abstractmethod
    async def handle_event(self, event_type: EventType, **data: Any) -> None:
        """Handle an event.

        Args:
            event_type: Type of event
            **data: Event data
        """
        pass


__all__ = ["EventHandler"]
