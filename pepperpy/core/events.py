"""Core events module.

This module provides the base event system for the framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


@dataclass
class Event:
    """Base class for all events.

    This class defines the common attributes and methods that all events must have.
    Events are used to notify components about changes in the system.
    """

    def __str__(self) -> str:
        """Get string representation of the event.

        Returns:
            String representation
        """
        return f"{self.__class__.__name__}"


class EventHandler(ABC):
    """Base class for event handlers.

    This class defines the interface that all event handlers must implement.
    Event handlers are responsible for processing events and taking appropriate actions.
    """

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Handle an event.

        Args:
            event: Event to handle
        """
        pass
