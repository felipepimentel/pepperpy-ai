"""Data update implementation."""

import logging
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ...common.errors import PepperpyError
from ...core.lifecycle import Lifecycle
from .algorithms.base_algorithm import Algorithm


logger = logging.getLogger(__name__)


class UpdateError(PepperpyError):
    """Update error."""
    pass


class Store(Protocol):
    """Data store protocol."""
    
    async def read(
        self,
        key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Read data from store.
        
        Args:
            key: Data key
            context: Optional read context
            
        Returns:
            Stored data
            
        Raises:
            UpdateError: If data cannot be read
        """
        ...
        
    async def write(
        self,
        key: str,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write data to store.
        
        Args:
            key: Data key
            data: Data to write
            context: Optional write context
            
        Raises:
            UpdateError: If data cannot be written
        """
        ...
        
    async def delete(
        self,
        key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Delete data from store.
        
        Args:
            key: Data key
            context: Optional delete context
            
        Raises:
            UpdateError: If data cannot be deleted
        """
        ...


T = TypeVar("T", bound=Store)


class UpdateManager(Lifecycle):
    """Data update manager implementation."""
    
    def __init__(
        self,
        name: str,
        store: Store,
        algorithms: Optional[List[Algorithm]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize update manager.
        
        Args:
            name: Manager name
            store: Data store
            algorithms: Optional processing algorithms
            config: Optional manager configuration
        """
        super().__init__(name)
        self._store = store
        self._algorithms = algorithms or []
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return manager configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize manager."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up manager."""
        pass
        
    async def update(
        self,
        key: str,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update data in store.
        
        Args:
            key: Data key
            data: Data to update
            context: Optional update context
            
        Raises:
            UpdateError: If data cannot be updated
        """
        try:
            # Process data
            result = data
            for algorithm in self._algorithms:
                result = await algorithm.process(result, context)
                
            # Write to store
            await self._store.write(key, result, context)
            
        except Exception as e:
            raise UpdateError(f"Failed to update data: {e}") from e
            
    async def delete(
        self,
        key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Delete data from store.
        
        Args:
            key: Data key
            context: Optional delete context
            
        Raises:
            UpdateError: If data cannot be deleted
        """
        try:
            await self._store.delete(key, context)
            
        except Exception as e:
            raise UpdateError(f"Failed to delete data: {e}") from e
            
    async def get(
        self,
        key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Get data from store.
        
        Args:
            key: Data key
            context: Optional get context
            
        Returns:
            Stored data
            
        Raises:
            UpdateError: If data cannot be retrieved
        """
        try:
            return await self._store.read(key, context)
            
        except Exception as e:
            raise UpdateError(f"Failed to get data: {e}") from e
            
    def validate(self) -> None:
        """Validate manager state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Manager name cannot be empty")
            
        if not self._store:
            raise ValueError("Data store not provided")


class FileStore(Store):
    """File data store implementation."""
    
    def __init__(
        self,
        base_path: str,
        encoding: str = "utf-8",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize file store.
        
        Args:
            base_path: Base path for files
            encoding: File encoding (default: utf-8)
            config: Optional store configuration
        """
        self._base_path = base_path
        self._encoding = encoding
        self._config = config or {}
        
    def _get_path(self, key: str) -> str:
        """Get file path for key.
        
        Args:
            key: Data key
            
        Returns:
            File path
        """
        return f"{self._base_path}/{key}"
        
    async def read(
        self,
        key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Read data from file.
        
        Args:
            key: Data key
            context: Optional read context
            
        Returns:
            File contents
            
        Raises:
            UpdateError: If file cannot be read
        """
        try:
            with open(self._get_path(key), "r", encoding=self._encoding) as f:
                return f.read()
                
        except Exception as e:
            raise UpdateError(f"Failed to read file: {e}") from e
            
    async def write(
        self,
        key: str,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write data to file.
        
        Args:
            key: Data key
            data: Data to write
            context: Optional write context
            
        Raises:
            UpdateError: If data cannot be written
        """
        try:
            with open(self._get_path(key), "w", encoding=self._encoding) as f:
                f.write(str(data))
                
        except Exception as e:
            raise UpdateError(f"Failed to write file: {e}") from e
            
    async def delete(
        self,
        key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Delete file.
        
        Args:
            key: Data key
            context: Optional delete context
            
        Raises:
            UpdateError: If file cannot be deleted
        """
        try:
            import os
            os.remove(self._get_path(key))
            
        except Exception as e:
            raise UpdateError(f"Failed to delete file: {e}") from e
