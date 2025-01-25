"""
Component initialization management for Pepperpy.
"""
from typing import Any, Dict, Optional, Type

from pepperpy.core.utils.errors import PepperpyError


class InitializationError(PepperpyError):
    """Error raised during component initialization."""
    pass


class Initializer:
    """Manages component initialization in the Pepperpy system."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the Initializer.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self._initialized_components: Dict[str, Any] = {}

    def initialize_component(self, component_class: Type[Any], **kwargs: Any) -> Any:
        """Initialize a component with the given configuration.

        Args:
            component_class: The class of the component to initialize.
            **kwargs: Additional initialization parameters.

        Returns:
            The initialized component instance.

        Raises:
            InitializationError: If initialization fails.
        """
        try:
            component_name = component_class.__name__
            if component_name in self._initialized_components:
                return self._initialized_components[component_name]

            component_config = {
                **self.config.get(component_name, {}),
                **kwargs
            }
            
            instance = component_class(**component_config)
            self._initialized_components[component_name] = instance
            return instance
        except Exception as e:
            raise InitializationError(
                f"Failed to initialize component {component_class.__name__}: {str(e)}"
            ) from e

    def get_initialized_component(self, component_name: str) -> Optional[Any]:
        """Get an initialized component by name.

        Args:
            component_name: Name of the component.

        Returns:
            The initialized component instance or None if not found.
        """
        return self._initialized_components.get(component_name)

    def reset(self) -> None:
        """Reset the initializer state."""
        self._initialized_components.clear() 