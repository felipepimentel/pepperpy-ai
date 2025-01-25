"""Data store functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


class DataStoreError(PepperpyError):
    """Data store error."""
    pass


class DataStore(Lifecycle, ABC):
    """Base class for data stores."""
    
    def __init__(self, name: str):
        """Initialize data store.
        
        Args:
            name: Data store name
        """
        super().__init__()
        self.name = name
        
    @abstractmethod
    async def get(self, key: str) -> Any:
        """Get value by key.
        
        Args:
            key: Key to get
            
        Returns:
            Value for key
            
        Raises:
            DataStoreError: If get fails
        """
        pass
        
    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """Set value for key.
        
        Args:
            key: Key to set
            value: Value to set
            
        Raises:
            DataStoreError: If set fails
        """
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete key.
        
        Args:
            key: Key to delete
            
        Raises:
            DataStoreError: If delete fails
        """
        pass
        
    @abstractmethod
    async def exists(self, key: str) -> bool:
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
        """Clear all keys.
        
        Raises:
            DataStoreError: If clear fails
        """
        pass
        
    def validate(self) -> None:
        """Validate data store state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Data store name cannot be empty") 