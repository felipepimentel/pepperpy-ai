"""Lifecycle management module for Pepperpy framework."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ...common.errors import PepperpyError


class LifecycleError(PepperpyError):
    """Lifecycle error class."""
    pass


class Lifecycle(ABC):
    """Base class for components with lifecycle management.
    
    All components that need lifecycle management should inherit from this class.
    """
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize lifecycle component.
        
        Args:
            name: Component name.
            config: Optional configuration dictionary.
            
        Raises:
            LifecycleError: If initialization fails.
        """
        self._name = name
        self._config = config or {}
        self._is_initialized = False
        
        if not self._name:
            raise LifecycleError("Component name cannot be empty")
        
        if not isinstance(self._config, dict):
            raise LifecycleError("Configuration must be a dictionary")

    @property
    def name(self) -> str:
        """Get component name."""
        return self._name

    @property
    def config(self) -> Dict[str, Any]:
        """Get component configuration."""
        return self._config

    @property
    def is_initialized(self) -> bool:
        """Check if component is initialized."""
        return self._is_initialized

    async def initialize(self) -> None:
        """Initialize component.
        
        Raises:
            LifecycleError: If initialization fails.
        """
        if self._is_initialized:
            raise LifecycleError(f"Component {self._name} is already initialized")
        
        try:
            await self._initialize_impl()
            self._is_initialized = True
        except Exception as e:
            raise LifecycleError(f"Failed to initialize component {self._name}: {e}")

    async def cleanup(self) -> None:
        """Clean up component resources.
        
        Raises:
            LifecycleError: If cleanup fails.
        """
        if not self._is_initialized:
            raise LifecycleError(f"Component {self._name} is not initialized")
        
        try:
            await self._cleanup_impl()
            self._is_initialized = False
        except Exception as e:
            raise LifecycleError(f"Failed to clean up component {self._name}: {e}")

    async def validate(self) -> None:
        """Validate component state.
        
        Raises:
            LifecycleError: If validation fails.
        """
        try:
            await self._validate_impl()
        except Exception as e:
            raise LifecycleError(f"Failed to validate component {self._name}: {e}")

    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Implementation of component initialization.
        
        Raises:
            Exception: If initialization fails.
        """
        pass

    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Implementation of component cleanup.
        
        Raises:
            Exception: If cleanup fails.
        """
        pass

    @abstractmethod
    async def _validate_impl(self) -> None:
        """Implementation of component validation.
        
        Raises:
            Exception: If validation fails.
        """
        pass 