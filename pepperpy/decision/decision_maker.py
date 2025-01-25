"""Decision maker implementation.

This module provides functionality for making decisions based on various
strategies and criteria, including validation and logging.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from .criteria import DecisionCriteria
from .strategy import DecisionStrategy

T = TypeVar("T")


class DecisionError(PepperpyError):
    """Decision error."""
    pass


class Decision(Generic[T]):
    """Decision result."""
    
    def __init__(
        self,
        value: T,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize decision.
        
        Args:
            value: Decision value
            confidence: Decision confidence (0-1)
            metadata: Optional metadata
        """
        self.value = value
        self.confidence = confidence
        self.metadata = metadata or {}
        
    def __str__(self) -> str:
        """Get string representation.
        
        Returns:
            String representation
        """
        return f"Decision(value={self.value}, confidence={self.confidence})"


class DecisionMaker(Lifecycle, ABC):
    """Decision maker implementation."""
    
    def __init__(
        self,
        name: str,
        strategy: DecisionStrategy,
        criteria: Optional[List[DecisionCriteria]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize maker.
        
        Args:
            name: Maker name
            strategy: Decision strategy
            criteria: Optional decision criteria
            config: Optional configuration
        """
        super().__init__()
        self.name = name
        self._strategy = strategy
        self._criteria = criteria or []
        self._config = config or {}
        
    @property
    def strategy(self) -> DecisionStrategy:
        """Get decision strategy.
        
        Returns:
            Decision strategy
        """
        return self._strategy
        
    @property
    def criteria(self) -> List[DecisionCriteria]:
        """Get decision criteria.
        
        Returns:
            Decision criteria
        """
        return self._criteria
        
    async def decide(self, context: Dict[str, Any]) -> Decision[T]:
        """Make decision.
        
        Args:
            context: Decision context
            
        Returns:
            Decision result
            
        Raises:
            DecisionError: If decision fails
        """
        self.validate()
        
        # Validate criteria
        for criterion in self._criteria:
            if not criterion.is_satisfied(context):
                raise DecisionError(
                    f"Decision criteria not satisfied: {criterion}"
                )
                
        # Make decision
        try:
            value, confidence = await self._strategy.evaluate(context)
            return Decision(value, confidence)
        except Exception as e:
            raise DecisionError(f"Decision failed: {e}")
            
    async def _initialize(self) -> None:
        """Initialize maker."""
        await self._strategy.initialize()
        
    async def _cleanup(self) -> None:
        """Clean up maker."""
        await self._strategy.cleanup()
        
    def validate(self) -> None:
        """Validate maker state."""
        if not self.name:
            raise DecisionError("Empty maker name")
            
        if not self._strategy:
            raise DecisionError("Missing decision strategy")
            
        self._strategy.validate() 