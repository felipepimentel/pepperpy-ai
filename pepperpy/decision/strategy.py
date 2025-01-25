"""Decision strategy implementation.

This module provides functionality for defining and evaluating decision
strategies, including validation and composition.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Generic

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle

T = TypeVar("T")


class StrategyError(PepperpyError):
    """Strategy error."""
    pass


class DecisionStrategy(Lifecycle, Generic[T], ABC):
    """Decision strategy interface."""
    
    def __init__(self, name: str) -> None:
        """Initialize strategy.
        
        Args:
            name: Strategy name
        """
        super().__init__()
        self.name = name
        
    @abstractmethod
    async def evaluate(self, context: Dict[str, Any]) -> Tuple[T, float]:
        """Evaluate decision.
        
        Args:
            context: Decision context
            
        Returns:
            Tuple of (decision value, confidence)
            
        Raises:
            StrategyError: If evaluation fails
        """
        pass
        
    async def _initialize(self) -> None:
        """Initialize strategy."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up strategy."""
        pass
        
    def validate(self) -> None:
        """Validate strategy state."""
        if not self.name:
            raise StrategyError("Empty strategy name")


class CompositeStrategy(DecisionStrategy[T]):
    """Composite decision strategy."""
    
    def __init__(
        self,
        name: str,
        strategies: List[DecisionStrategy[T]],
        weights: Optional[List[float]] = None,
    ) -> None:
        """Initialize strategy.
        
        Args:
            name: Strategy name
            strategies: Child strategies
            weights: Optional strategy weights
        """
        super().__init__(name)
        self._strategies = strategies
        self._weights = weights or [1.0] * len(strategies)
        
        if len(self._weights) != len(strategies):
            raise StrategyError("Mismatched strategy and weight counts")
            
        if not all(w >= 0 for w in self._weights):
            raise StrategyError("Invalid strategy weights")
            
        total = sum(self._weights)
        if total > 0:
            self._weights = [w / total for w in self._weights]
            
    async def evaluate(self, context: Dict[str, Any]) -> Tuple[T, float]:
        """Evaluate decision.
        
        Args:
            context: Decision context
            
        Returns:
            Tuple of (decision value, confidence)
            
        Raises:
            StrategyError: If evaluation fails
        """
        if not self._strategies:
            raise StrategyError("No strategies to evaluate")
            
        results = []
        for strategy, weight in zip(self._strategies, self._weights):
            try:
                value, confidence = await strategy.evaluate(context)
                results.append((value, confidence * weight))
            except Exception as e:
                raise StrategyError(f"Strategy evaluation failed: {e}")
                
        # Select result with highest weighted confidence
        best_result = max(results, key=lambda r: r[1])
        return best_result
        
    async def _initialize(self) -> None:
        """Initialize strategy."""
        for strategy in self._strategies:
            await strategy.initialize()
            
    async def _cleanup(self) -> None:
        """Clean up strategy."""
        for strategy in self._strategies:
            await strategy.cleanup()
            
    def validate(self) -> None:
        """Validate strategy state."""
        super().validate()
        
        for strategy in self._strategies:
            strategy.validate() 