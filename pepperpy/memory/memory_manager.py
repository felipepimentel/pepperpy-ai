"""Memory manager module for Pepperpy framework."""

from typing import Any, Dict, List, Optional, Type

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.memory.base import MemorySystem
from pepperpy.core.lifecycle import Lifecycle


class MemoryManagerError(PepperpyError):
    """Memory manager error class."""
    pass


class MemoryManager(Lifecycle):
    """Memory manager class.
    
    This class manages memory systems and their operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize memory manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self._config = config or {}
        self._memory_systems: Dict[str, MemorySystem] = {}
        self._is_initialized = False
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get memory manager configuration."""
        return self._config
    
    @property
    def is_initialized(self) -> bool:
        """Check if memory manager is initialized."""
        return self._is_initialized
    
    def register_memory_system(
        self,
        name: str,
        memory_system: MemorySystem
    ) -> None:
        """Register a memory system.
        
        Args:
            name: Memory system name
            memory_system: Memory system instance
            
        Raises:
            MemoryManagerError: If registration fails
        """
        if name in self._memory_systems:
            raise MemoryManagerError(f"Memory system {name} is already registered")
        
        if not isinstance(memory_system, MemorySystem):
            raise MemoryManagerError(
                f"Memory system {name} must be a MemorySystem instance"
            )
        
        self._memory_systems[name] = memory_system
    
    def get_memory_system(self, name: str) -> MemorySystem:
        """Get a memory system by name.
        
        Args:
            name: Memory system name
            
        Returns:
            Memory system instance
            
        Raises:
            MemoryManagerError: If memory system not found
        """
        if name not in self._memory_systems:
            raise MemoryManagerError(f"Memory system {name} not found")
        
        return self._memory_systems[name]
    
    def list_memory_systems(self) -> List[str]:
        """List all registered memory systems.
        
        Returns:
            List of memory system names
        """
        return list(self._memory_systems.keys())
    
    async def initialize(self) -> None:
        """Initialize memory manager and all memory systems.
        
        Raises:
            MemoryManagerError: If initialization fails
        """
        if self.is_initialized:
            return
        
        try:
            for name, memory_system in self._memory_systems.items():
                await memory_system.initialize()
            self._is_initialized = True
        except Exception as e:
            await self.cleanup()
            raise MemoryManagerError(f"Failed to initialize memory manager: {e}")
    
    async def cleanup(self) -> None:
        """Clean up memory manager and all memory systems.
        
        Raises:
            MemoryManagerError: If cleanup fails
        """
        if not self.is_initialized:
            return
        
        try:
            for name, memory_system in self._memory_systems.items():
                await memory_system.cleanup()
            self._is_initialized = False
        except Exception as e:
            raise MemoryManagerError(f"Failed to clean up memory manager: {e}")
    
    async def store(
        self,
        memory_system: str,
        key: str,
        value: Any
    ) -> None:
        """Store value in memory system.
        
        Args:
            memory_system: Memory system name
            key: Key to store value under
            value: Value to store
            
        Raises:
            MemoryManagerError: If storing fails
        """
        if not self.is_initialized:
            raise MemoryManagerError("Memory manager not initialized")
        
        try:
            system = self.get_memory_system(memory_system)
            await system.store(key, value)
        except Exception as e:
            raise MemoryManagerError(f"Failed to store value: {e}")
    
    async def retrieve(
        self,
        memory_system: str,
        key: str
    ) -> Optional[Any]:
        """Retrieve value from memory system.
        
        Args:
            memory_system: Memory system name
            key: Key to retrieve value for
            
        Returns:
            Retrieved value or None if not found
            
        Raises:
            MemoryManagerError: If retrieval fails
        """
        if not self.is_initialized:
            raise MemoryManagerError("Memory manager not initialized")
        
        try:
            system = self.get_memory_system(memory_system)
            return await system.retrieve(key)
        except Exception as e:
            raise MemoryManagerError(f"Failed to retrieve value: {e}")
    
    async def delete(
        self,
        memory_system: str,
        key: str
    ) -> None:
        """Delete value from memory system.
        
        Args:
            memory_system: Memory system name
            key: Key to delete value for
            
        Raises:
            MemoryManagerError: If deletion fails
        """
        if not self.is_initialized:
            raise MemoryManagerError("Memory manager not initialized")
        
        try:
            system = self.get_memory_system(memory_system)
            await system.delete(key)
        except Exception as e:
            raise MemoryManagerError(f"Failed to delete value: {e}")
    
    async def clear(self, memory_system: str) -> None:
        """Clear all values from memory system.
        
        Args:
            memory_system: Memory system name
            
        Raises:
            MemoryManagerError: If clearing fails
        """
        if not self.is_initialized:
            raise MemoryManagerError("Memory manager not initialized")
        
        try:
            system = self.get_memory_system(memory_system)
            await system.clear()
        except Exception as e:
            raise MemoryManagerError(f"Failed to clear memory system: {e}")
    
    async def list_keys(self, memory_system: str) -> List[str]:
        """List all keys in memory system.
        
        Args:
            memory_system: Memory system name
            
        Returns:
            List of keys
            
        Raises:
            MemoryManagerError: If listing fails
        """
        if not self.is_initialized:
            raise MemoryManagerError("Memory manager not initialized")
        
        try:
            system = self.get_memory_system(memory_system)
            return await system.list_keys()
        except Exception as e:
            raise MemoryManagerError(f"Failed to list keys: {e}") 