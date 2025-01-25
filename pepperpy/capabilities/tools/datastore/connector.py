"""Data store connector functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from .datastore import DataStore


class ConnectorError(PepperpyError):
    """Connector error."""
    pass


class DataStoreConnector(Lifecycle, ABC):
    """Base class for data store connectors."""
    
    def __init__(self, name: str):
        """Initialize connector.
        
        Args:
            name: Connector name
        """
        super().__init__()
        self.name = name
        self._store: Optional[DataStore] = None
        
    @property
    def store(self) -> Optional[DataStore]:
        """Get connected data store."""
        return self._store
        
    @abstractmethod
    async def connect(self, **kwargs: Any) -> None:
        """Connect to data store.
        
        Args:
            **kwargs: Connection arguments
            
        Raises:
            ConnectorError: If connection fails
        """
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from data store.
        
        Raises:
            ConnectorError: If disconnection fails
        """
        pass
        
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if connected to data store.
        
        Returns:
            True if connected, False otherwise
            
        Raises:
            ConnectorError: If check fails
        """
        pass
        
    def validate(self) -> None:
        """Validate connector state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Connector name cannot be empty") 