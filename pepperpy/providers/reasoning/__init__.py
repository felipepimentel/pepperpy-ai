"""Reasoning module for implementing logical frameworks.

This module provides various reasoning frameworks and evaluation metrics for
logical processes, including Chain-of-Thought (CoT) and ReAct implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.reasoning.frameworks.cot import CoTAgent, CoTStep
from pepperpy.reasoning.frameworks.react import ReActAgent, ReActStep

logger = logging.getLogger(__name__)


class ReasoningError(PepperpyError):
    """Reasoning error."""
    pass


class Reasoner(Lifecycle, ABC):
    """Reasoner implementation."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize reasoner.
        
        Args:
            name: Reasoner name
            config: Optional reasoner configuration
        """
        super().__init__(name)
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return reasoner configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize reasoner."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up reasoner."""
        pass
        
    @abstractmethod
    async def reason(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Reason about input data.
        
        Args:
            input_data: Input data
            context: Optional reasoning context
            
        Returns:
            Reasoning result
        """
        pass
        
    def validate(self) -> None:
        """Validate reasoner state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Reasoner name cannot be empty")


__all__ = [
    "ReasoningError",
    "Reasoner",
    "CoTAgent",
    "CoTStep",
    "ReActAgent", 
    "ReActStep",
]
