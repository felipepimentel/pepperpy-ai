"""Base component classes and interfaces for Pepperpy."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Set, Type, TypeVar

from ...common.constants import Status
from ...common.types import (
    PepperpyObject,
    DictInitializable,
    Validatable,
    ContextManageable,
    Disposable,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="Component")

class Component(PepperpyObject, DictInitializable, Validatable, ContextManageable, Disposable, ABC):
    """Base class for all Pepperpy components."""
    
    def __init__(self, name: str) -> None:
        """Initialize component.
        
        Args:
            name: Component name
        """
        self._name = name
        self._status = Status.PENDING
        self._dependencies: Set[Component] = set()
        self._lock = asyncio.Lock()
        
    @property
    def name(self) -> str:
        """Return component name."""
        return self._name
        
    @property
    def status(self) -> Status:
        """Return component status."""
        return self._status
        
    @property
    def dependencies(self) -> Set["Component"]:
        """Return component dependencies."""
        return self._dependencies
        
    def add_dependency(self, component: "Component") -> None:
        """Add dependency to component.
        
        Args:
            component: Component to add as dependency
        """
        self._dependencies.add(component)
        
    def remove_dependency(self, component: "Component") -> None:
        """Remove dependency from component.
        
        Args:
            component: Component to remove from dependencies
        """
        self._dependencies.discard(component)
        
    async def initialize(self) -> None:
        """Initialize component and its dependencies."""
        async with self._lock:
            if self._status != Status.PENDING:
                return
                
            self._status = Status.RUNNING
            
            try:
                # Initialize dependencies first
                for dependency in self._dependencies:
                    await dependency.initialize()
                    
                # Initialize self
                await self._initialize()
                self._status = Status.COMPLETED
                logger.info(f"Component {self.name} initialized successfully")
                
            except Exception as e:
                self._status = Status.FAILED
                logger.error(f"Failed to initialize component {self.name}: {str(e)}")
                raise
                
    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize component implementation."""
        ...
        
    async def dispose(self) -> None:
        """Dispose of component resources."""
        async with self._lock:
            if self._status not in {Status.COMPLETED, Status.FAILED}:
                return
                
            try:
                # Dispose self first
                await self._dispose()
                
                # Then dispose dependencies
                for dependency in self._dependencies:
                    await dependency.dispose()
                    
                self._status = Status.CANCELLED
                logger.info(f"Component {self.name} disposed successfully")
                
            except Exception as e:
                logger.error(f"Failed to dispose component {self.name}: {str(e)}")
                raise
                
    @abstractmethod
    async def _dispose(self) -> None:
        """Dispose component implementation."""
        ...
        
    async def __aenter__(self) -> "Component":
        """Enter async context."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self.dispose()
        
    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(name={self.name}, status={self.status})"
        
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create component from dictionary.
        
        Args:
            data: Dictionary with component data
            
        Returns:
            Component instance
        """
        return cls(name=data["name"])
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary.
        
        Returns:
            Dictionary with component data
        """
        return {
            "name": self.name,
            "status": self.status,
        }
        
    def validate(self) -> None:
        """Validate component state."""
        if not self.name:
            raise ValueError("Component name cannot be empty") 