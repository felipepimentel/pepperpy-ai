"""In-memory store implementation."""

import logging
from typing import Any, Dict, Optional, TypeVar

from .base import DataStore, DataStoreError


logger = logging.getLogger(__name__)


T = TypeVar("T")


class InMemoryStore(DataStore):
    """In-memory store implementation."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize in-memory store.
        
        Args:
            name: Store name
            config: Optional store configuration
        """
        super().__init__(name, config)
        self._data: Dict[str, Any] = {}
        
    async def _initialize(self) -> None:
        """Initialize in-memory store."""
        await super()._initialize()
        
    async def _cleanup(self) -> None:
        """Clean up in-memory store."""
        await super()._cleanup()
        self._data.clear()
        
    async def get(
        self,
        key: str,
        default: Optional[Any] = None,
    ) -> Optional[Any]:
        """Get value by key.
        
        Args:
            key: Key to get
            default: Optional default value
            
        Returns:
            Value if found, default otherwise
            
        Raises:
            DataStoreError: If retrieval fails
        """
        try:
            return self._data.get(key, default)
        except Exception as e:
            raise DataStoreError(f"Failed to get value for key {key}: {e}") from e
            
    async def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Set value by key.
        
        Args:
            key: Key to set
            value: Value to set
            
        Raises:
            DataStoreError: If setting fails
        """
        try:
            self._data[key] = value
        except Exception as e:
            raise DataStoreError(f"Failed to set value for key {key}: {e}") from e
            
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
        try:
            if key in self._data:
                del self._data[key]
        except Exception as e:
            raise DataStoreError(f"Failed to delete key {key}: {e}") from e
            
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
        try:
            return key in self._data
        except Exception as e:
            raise DataStoreError(f"Failed to check key {key}: {e}") from e
            
    async def clear(self) -> None:
        """Clear all values.
        
        Raises:
            DataStoreError: If clearing fails
        """
        try:
            self._data.clear()
        except Exception as e:
            raise DataStoreError(f"Failed to clear store: {e}") from e 