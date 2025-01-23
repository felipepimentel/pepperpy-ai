"""Lifecycle implementation.

This module provides functionality for managing component lifecycles,
including initialization, cleanup, and state validation.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, Optional

from pepperpy.common.errors import PepperpyError


class LifecycleState(Enum):
    """Lifecycle states."""
    
    UNINITIALIZED = auto()
    """Component is uninitialized."""
    
    INITIALIZING = auto()
    """Component is initializing."""
    
    INITIALIZED = auto()
    """Component is initialized."""
    
    CLEANING_UP = auto()
    """Component is cleaning up."""
    
    CLEANED_UP = auto()
    """Component is cleaned up."""
    
    ERROR = auto()
    """Component is in error state."""


class LifecycleError(PepperpyError):
    """Lifecycle error."""
    pass


class Lifecycle(ABC):
    """Lifecycle interface."""
    
    def __init__(self) -> None:
        """Initialize lifecycle."""
        self._state = LifecycleState.UNINITIALIZED
        self._error: Optional[Exception] = None
        
    @property
    def state(self) -> LifecycleState:
        """Get lifecycle state.
        
        Returns:
            Lifecycle state
        """
        return self._state
        
    @property
    def error(self) -> Optional[Exception]:
        """Get lifecycle error.
        
        Returns:
            Lifecycle error if any
        """
        return self._error
        
    @property
    def is_initialized(self) -> bool:
        """Check if initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._state == LifecycleState.INITIALIZED
        
    @property
    def is_error(self) -> bool:
        """Check if in error state.
        
        Returns:
            True if in error state, False otherwise
        """
        return self._state == LifecycleState.ERROR
        
    async def initialize(self) -> None:
        """Initialize component.
        
        Raises:
            LifecycleError: If initialization fails
        """
        if self._state != LifecycleState.UNINITIALIZED:
            raise LifecycleError(
                f"Invalid state for initialization: {self._state}"
            )
            
        try:
            self._state = LifecycleState.INITIALIZING
            await self._initialize()
            self._state = LifecycleState.INITIALIZED
        except Exception as e:
            self._error = e
            self._state = LifecycleState.ERROR
            raise LifecycleError(f"Initialization failed: {e}")
            
    async def cleanup(self) -> None:
        """Clean up component.
        
        Raises:
            LifecycleError: If cleanup fails
        """
        if self._state not in (
            LifecycleState.INITIALIZED,
            LifecycleState.ERROR,
        ):
            raise LifecycleError(f"Invalid state for cleanup: {self._state}")
            
        try:
            self._state = LifecycleState.CLEANING_UP
            await self._cleanup()
            self._state = LifecycleState.CLEANED_UP
        except Exception as e:
            self._error = e
            self._state = LifecycleState.ERROR
            raise LifecycleError(f"Cleanup failed: {e}")
            
    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize component.
        
        Raises:
            Exception: If initialization fails
        """
        pass
        
    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up component.
        
        Raises:
            Exception: If cleanup fails
        """
        pass
        
    def validate(self) -> None:
        """Validate component state.
        
        Raises:
            LifecycleError: If validation fails
        """
        if self._state == LifecycleState.ERROR and self._error:
            raise LifecycleError(f"Component in error state: {self._error}")
            
        if self._state not in (
            LifecycleState.INITIALIZED,
            LifecycleState.CLEANED_UP,
        ):
            raise LifecycleError(f"Invalid component state: {self._state}") 