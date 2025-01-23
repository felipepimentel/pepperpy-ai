"""Base data store implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


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
        super().__init__()
        self.name = name
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get store configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize store."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up store."""
        pass
        
    @abstractmethod
    async def get(
        self,
        key: str,
        default: Optional[T] = None,
    ) -> Optional[T]:
        """Get value by key.
        
        Args:
            key: Storage key
            default: Default value if key not found
            
        Returns:
            Retrieved value or default if not found
            
        Raises:
            DataStoreError: If storage operation fails
        """
        pass
        
    @abstractmethod
    async def set(
        self,
        key: str,
        value: T,
    ) -> None:
        """Set value for key.
        
        Args:
            key: Storage key
            value: Value to store
            
        Raises:
            DataStoreError: If storage operation fails
        """
        pass
        
    @abstractmethod
    async def delete(
        self,
        key: str,
    ) -> None:
        """Delete value by key.
        
        Args:
            key: Storage key
            
        Raises:
            DataStoreError: If storage operation fails
        """
        pass
        
    @abstractmethod
    async def exists(
        self,
        key: str,
    ) -> bool:
        """Check if key exists.
        
        Args:
            key: Storage key
            
        Returns:
            True if key exists, False otherwise
            
        Raises:
            DataStoreError: If storage operation fails
        """
        pass
        
    @abstractmethod
    async def clear(self) -> None:
        """Clear all values.
        
        Raises:
            DataStoreError: If storage operation fails
        """
        pass
        
    def validate(self) -> None:
        """Validate store state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Store name cannot be empty") 