"""Runtime state management for Pepperpy.

This module provides functionality for managing runtime state, including
state transitions, persistence, and recovery.
"""

import logging
from typing import Any, Dict, Optional, Protocol, TypeVar

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class StateError(PepperpyError):
    """State error."""
    pass


T = TypeVar("T")


class State(Protocol[T]):
    """State protocol."""
    
    @property
    def data(self) -> T:
        """Get state data."""
        raise NotImplementedError
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get state metadata."""
        raise NotImplementedError


class StateManager(Lifecycle):
    """Runtime state manager."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize state manager.
        
        Args:
            name: State manager name
            config: Optional state manager configuration
        """
        super().__init__()
        self.name = name
        self._config = config or {}
        self._states: Dict[str, Any] = {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get state manager configuration."""
        return self._config
        
    async def initialize(self) -> None:
        """Initialize state manager."""
        try:
            # Load persisted states
            for name, config in self._config.get("states", {}).items():
                self._states[name] = await self._load_state(name, config)
                
        except Exception as e:
            logger.error(f"Failed to initialize state manager: {e}")
            raise StateError(str(e))
            
    async def cleanup(self) -> None:
        """Clean up state manager."""
        try:
            # Persist states
            for name, state in self._states.items():
                await self._persist_state(name, state)
                
            self._states.clear()
            
        except Exception as e:
            logger.error(f"Failed to clean up state manager: {e}")
            raise StateError(str(e))
            
    async def get_state(self, name: str) -> Optional[Any]:
        """Get state by name.
        
        Args:
            name: State name
            
        Returns:
            State if found, None otherwise
            
        Raises:
            StateError: If state retrieval fails
        """
        try:
            return self._states.get(name)
            
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            raise StateError(str(e))
            
    async def set_state(self, name: str, state: Any) -> None:
        """Set state by name.
        
        Args:
            name: State name
            state: State to set
            
        Raises:
            StateError: If state update fails
        """
        try:
            self._states[name] = state
            await self._persist_state(name, state)
            
        except Exception as e:
            logger.error(f"Failed to set state: {e}")
            raise StateError(str(e))
            
    async def delete_state(self, name: str) -> None:
        """Delete state by name.
        
        Args:
            name: State name
            
        Raises:
            StateError: If state deletion fails
        """
        try:
            if name in self._states:
                del self._states[name]
                await self._delete_persisted_state(name)
                
        except Exception as e:
            logger.error(f"Failed to delete state: {e}")
            raise StateError(str(e))
            
    async def _load_state(
        self,
        name: str,
        config: Dict[str, Any],
    ) -> Any:
        """Load persisted state.
        
        Args:
            name: State name
            config: State configuration
            
        Returns:
            Loaded state
            
        Raises:
            StateError: If state loading fails
        """
        raise NotImplementedError
        
    async def _persist_state(
        self,
        name: str,
        state: Any,
    ) -> None:
        """Persist state.
        
        Args:
            name: State name
            state: State to persist
            
        Raises:
            StateError: If state persistence fails
        """
        raise NotImplementedError
        
    async def _delete_persisted_state(
        self,
        name: str,
    ) -> None:
        """Delete persisted state.
        
        Args:
            name: State name
            
        Raises:
            StateError: If state deletion fails
        """
        raise NotImplementedError
        
    def validate(self) -> None:
        """Validate state manager state."""
        super().validate()
        
        if not self.name:
            raise ValueError("State manager name cannot be empty") 