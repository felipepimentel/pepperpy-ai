"""Base data store implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ...common.errors import PepperpyError
from ...core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class DataStoreError(PepperpyError):
    """Data store error."""
    pass


T = TypeVar("T")


class DataStore(Lifecycle, ABC):
    """Data store implementation."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize data store.
        
        Args:
            name: Store name
            config: Optional store configuration
        """
        super().__init__(name)
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return store configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize data store."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up data store."""
        pass
        
    @abstractmethod
    async def get(
        self,
        key: str,
        default: Optional[T] = None,
    ) -> Optional[T]:
        """Get value by key.
        
        Args:
            key: Key to get
            default: Optional default value
            
        Returns:
            Value if found, default otherwise
            
        Raises:
            DataStoreError: If retrieval fails
        """
        pass
        
    @abstractmethod
    async def set(
        self,
        key: str,
        value: T,
    ) -> None:
        """Set value by key.
        
        Args:
            key: Key to set
            value: Value to set
            
        Raises:
            DataStoreError: If setting fails
        """
        pass
        
    @abstractmethod
    async def delete(
        self,
        key: str,
    ) -> None:
        """Delete value by key.
        
        Args:
            key: Key to delete
            
        Raises:
            DataStoreError: If deletion fails
        """
        pass
        
    @abstractmethod
    async def exists(
        self,
        key: str,
    ) -> bool:
        """Check if key exists.
        
        Args:
            key: Key to check
            
        Returns:
            True if key exists, False otherwise
            
        Raises:
            DataStoreError: If check fails
        """
        pass
        
    @abstractmethod
    async def clear(self) -> None:
        """Clear all values.
        
        Raises:
            DataStoreError: If clearing fails
        """
        pass
        
    def validate(self) -> None:
        """Validate data store state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Store name cannot be empty") 