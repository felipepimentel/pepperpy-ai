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
        """Initialize store."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up store."""
        self._data.clear()
        
    async def get(
        self,
        key: str,
        default: Optional[Any] = None,
    ) -> Optional[Any]:
        """Get value by key.
        
        Args:
            key: Storage key
            default: Default value if key not found
            
        Returns:
            Retrieved value or default if not found
            
        Raises:
            DataStoreError: If storage operation fails
        """
        try:
            return self._data.get(key, default)
        except Exception as e:
            raise DataStoreError(f"Failed to get value: {e}")
            
    async def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Set value for key.
        
        Args:
            key: Storage key
            value: Value to store
            
        Raises:
            DataStoreError: If storage operation fails
        """
        try:
            self._data[key] = value
        except Exception as e:
            raise DataStoreError(f"Failed to set value: {e}")
            
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
        try:
            if key in self._data:
                del self._data[key]
        except Exception as e:
            raise DataStoreError(f"Failed to delete value: {e}")
            
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
        try:
            return key in self._data
        except Exception as e:
            raise DataStoreError(f"Failed to check key existence: {e}")
            
    async def clear(self) -> None:
        """Clear all values.
        
        Raises:
            DataStoreError: If storage operation fails
        """
        try:
            self._data.clear()
        except Exception as e:
            raise DataStoreError(f"Failed to clear store: {e}") 