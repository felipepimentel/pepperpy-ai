"""Base learning implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ..common.errors import PepperpyError
from ..core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class LearningError(PepperpyError):
    """Learning error."""
    pass


class LearningStrategy(Lifecycle, ABC):
    """Learning strategy implementation."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize learning strategy.
        
        Args:
            name: Strategy name
            config: Optional strategy configuration
        """
        super().__init__(name)
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return strategy configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize learning strategy."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up learning strategy."""
        pass
        
    @abstractmethod
    async def train(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Train on input data.
        
        Args:
            input_data: Input data
            context: Optional training context
            
        Returns:
            Training result
        """
        pass
        
    @abstractmethod
    async def evaluate(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Evaluate on input data.
        
        Args:
            input_data: Input data
            context: Optional evaluation context
            
        Returns:
            Evaluation result
        """
        pass
        
    def validate(self) -> None:
        """Validate learning strategy state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Strategy name cannot be empty") 