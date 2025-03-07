"""Base class for developer assistants."""

import abc
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from pepperpy.core.base import BaseComponent

T = TypeVar("T")


class BaseAssistant(BaseComponent, Generic[T], abc.ABC):
    """Base class for all developer assistants.

    Developer assistants help users create and configure PepperPy components
    through interactive guidance, templates, and automated setup.
    """

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        callbacks: Optional[Dict[str, Callable]] = None,
    ) -> None:
        """Initialize the assistant.

        Args:
            name: Name of the assistant
            config: Configuration for the assistant
            callbacks: Callback functions for assistant events
        """
        super().__init__()
        self._name = name
        self.config = config or {}
        self.callbacks = callbacks or {}
        self.history: List[Dict[str, Any]] = []
        self.interactive = self.config.get("interactive", True)
        self.verbose = self.config.get("verbose", True)

    @property
    def name(self) -> str:
        """Get the assistant name.

        Returns:
            The name of the assistant
        """
        return self._name

    @abc.abstractmethod
    def create(self, description: str, **kwargs: Any) -> T:
        """Create a component based on the description.

        Args:
            description: Description of what to create
            **kwargs: Additional parameters for creation

        Returns:
            The created component
        """
        pass

    @abc.abstractmethod
    def modify(self, component: T, description: str, **kwargs: Any) -> T:
        """Modify an existing component based on the description.

        Args:
            component: Component to modify
            description: Description of the modifications
            **kwargs: Additional parameters for modification

        Returns:
            The modified component
        """
        pass

    @abc.abstractmethod
    def explain(self, component: T, **kwargs: Any) -> str:
        """Explain a component.

        Args:
            component: Component to explain
            **kwargs: Additional parameters for explanation

        Returns:
            Explanation of the component
        """
        pass

    def _trigger_callback(self, event: str, data: Dict[str, Any]) -> None:
        """Trigger a callback if it exists.

        Args:
            event: Name of the event
            data: Data to pass to the callback
        """
        callback = self.callbacks.get(f"on_{event}")
        if callback and callable(callback):
            callback(data)

    def _add_to_history(self, action: str, data: Dict[str, Any]) -> None:
        """Add an action to the history.

        Args:
            action: Name of the action
            data: Data associated with the action
        """
        if self.config.get("save_history", True):
            self.history.append({"action": action, "data": data})

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the assistant's action history.

        Returns:
            List of actions performed by the assistant
        """
        return self.history
