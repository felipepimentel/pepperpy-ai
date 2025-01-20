"""Base learning strategy classes for Pepperpy."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from ...common.types import PepperpyObject, DictInitializable, Validatable
from ...common.errors import StorageError, LearningError
from ...core.lifecycle import Lifecycle
from ...core.context import Context

T = TypeVar("T")

class LearningStrategy(Lifecycle, Generic[T], ABC):
    """Base learning strategy class."""
    
    def __init__(
        self,
        name: str,
        context: Optional[Context] = None,
    ) -> None:
        """Initialize learning strategy.
        
        Args:
            name: Strategy name
            context: Optional execution context
        """
        super().__init__(name, context)
        self._initialized = False
        
    @property
    def is_initialized(self) -> bool:
        """Check if strategy is initialized."""
        return self._initialized
        
    async def _initialize(self) -> None:
        """Initialize strategy."""
        self._initialized = True
        
    async def _cleanup(self) -> None:
        """Clean up strategy."""
        self._initialized = False
        
    async def add_example(self, example: T) -> None:
        """Add example to strategy.
        
        Args:
            example: Example to add
            
        Raises:
            LearningError: If strategy is not initialized
        """
        if not self.is_initialized:
            raise LearningError("Strategy not initialized")
            
        await self._add_example(example)
        
    @abstractmethod
    async def _add_example(self, example: T) -> None:
        """Add example to strategy.
        
        Args:
            example: Example to add
        """
        pass
        
    async def execute(self, input_data: Any) -> Any:
        """Execute learning strategy.
        
        Args:
            input_data: Input data
            
        Returns:
            Strategy output
            
        Raises:
            LearningError: If strategy is not initialized
        """
        if not self.is_initialized:
            raise LearningError("Strategy not initialized")
            
        return await self._execute(input_data)
        
    @abstractmethod
    async def _execute(self, input_data: Any) -> Any:
        """Execute learning strategy.
        
        Args:
            input_data: Input data
            
        Returns:
            Strategy output
        """
        pass
        
    def validate(self) -> None:
        """Validate strategy state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Strategy name cannot be empty")
            
        if self._context is not None:
            self._context.validate() 