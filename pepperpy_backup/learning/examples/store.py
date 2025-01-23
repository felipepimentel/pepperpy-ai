"""Example store implementation."""

import logging
from typing import Any, Dict, List, Optional

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class ExampleStoreError(PepperpyError):
    """Example store error."""
    pass


class ExampleStore(Lifecycle):
    """Example store implementation."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize example store.
        
        Args:
            name: Store name
            config: Optional store configuration
        """
        super().__init__()
        self.name = name
        self._config = config or {}
        self._examples: Dict[str, Any] = {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get store configuration."""
        return self._config
        
    async def initialize(self) -> None:
        """Initialize store."""
        try:
            # Load examples from storage
            for name, config in self._config.get("examples", {}).items():
                self._examples[name] = await self._load_example(name, config)
                
        except Exception as e:
            logger.error(f"Failed to initialize example store: {e}")
            raise ExampleStoreError(str(e))
            
    async def cleanup(self) -> None:
        """Clean up store."""
        try:
            # Persist examples
            for name, example in self._examples.items():
                await self._persist_example(name, example)
                
            self._examples.clear()
            
        except Exception as e:
            logger.error(f"Failed to clean up example store: {e}")
            raise ExampleStoreError(str(e))
            
    async def add_example(
        self,
        name: str,
        example: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add example to store.
        
        Args:
            name: Example name
            example: Example data
            metadata: Optional example metadata
            
        Raises:
            ExampleStoreError: If example addition fails
        """
        try:
            self._examples[name] = {
                "data": example,
                "metadata": metadata or {},
            }
            await self._persist_example(name, self._examples[name])
            
        except Exception as e:
            logger.error(f"Failed to add example: {e}")
            raise ExampleStoreError(str(e))
            
    async def get_example(
        self,
        name: str,
    ) -> Optional[Dict[str, Any]]:
        """Get example by name.
        
        Args:
            name: Example name
            
        Returns:
            Example data if found, None otherwise
            
        Raises:
            ExampleStoreError: If example retrieval fails
        """
        try:
            return self._examples.get(name)
            
        except Exception as e:
            logger.error(f"Failed to get example: {e}")
            raise ExampleStoreError(str(e))
            
    async def delete_example(
        self,
        name: str,
    ) -> None:
        """Delete example by name.
        
        Args:
            name: Example name
            
        Raises:
            ExampleStoreError: If example deletion fails
        """
        try:
            if name in self._examples:
                del self._examples[name]
                await self._delete_persisted_example(name)
                
        except Exception as e:
            logger.error(f"Failed to delete example: {e}")
            raise ExampleStoreError(str(e))
            
    async def _load_example(
        self,
        name: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Load example from storage.
        
        Args:
            name: Example name
            config: Example configuration
            
        Returns:
            Example data
            
        Raises:
            ExampleStoreError: If example loading fails
        """
        raise NotImplementedError
        
    async def _persist_example(
        self,
        name: str,
        example: Dict[str, Any],
    ) -> None:
        """Persist example to storage.
        
        Args:
            name: Example name
            example: Example data
            
        Raises:
            ExampleStoreError: If example persistence fails
        """
        raise NotImplementedError
        
    async def _delete_persisted_example(
        self,
        name: str,
    ) -> None:
        """Delete persisted example.
        
        Args:
            name: Example name
            
        Raises:
            ExampleStoreError: If example deletion fails
        """
        raise NotImplementedError
        
    def validate(self) -> None:
        """Validate store state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Store name cannot be empty") 