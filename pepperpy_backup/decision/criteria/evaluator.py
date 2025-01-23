"""Decision criteria evaluator implementation."""

import logging
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ...common.errors import PepperpyError
from ...core.lifecycle import Lifecycle
from ...models.types import Message
from ..engine.core import Decision


logger = logging.getLogger(__name__)


class CriteriaError(PepperpyError):
    """Criteria error."""
    pass


class Criterion(Protocol):
    """Decision criterion protocol."""
    
    async def evaluate(
        self,
        decision: Decision,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> float:
        """Evaluate decision against criterion.
        
        Args:
            decision: Decision to evaluate
            context: Decision context
            messages: Input messages
            
        Returns:
            Score between 0 and 1
            
        Raises:
            CriteriaError: If criterion cannot be evaluated
        """
        ...


C = TypeVar("C", bound=Criterion)


class CriteriaEvaluator(Lifecycle):
    """Decision criteria evaluator."""
    
    def __init__(
        self,
        name: str,
        criteria: List[Criterion],
        weights: Optional[List[float]] = None,
        min_score: float = 0.0,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize evaluator.
        
        Args:
            name: Evaluator name
            criteria: Evaluation criteria
            weights: Optional criterion weights (default: equal weights)
            min_score: Minimum evaluation score (default: 0.0)
            config: Optional evaluator configuration
        """
        super().__init__(name)
        self._criteria = criteria
        self._weights = self._normalize_weights(weights or [1.0] * len(criteria))
        self._min_score = min_score
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return evaluator configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize evaluator."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up evaluator."""
        pass
        
    async def evaluate(
        self,
        decisions: List[Decision],
        context: Dict[str, Any],
        messages: List[Message],
    ) -> List[Decision]:
        """Evaluate decisions against criteria.
        
        Args:
            decisions: Decisions to evaluate
            context: Decision context
            messages: Input messages
            
        Returns:
            List of decisions that meet criteria
            
        Raises:
            CriteriaError: If decisions cannot be evaluated
        """
        try:
            # Evaluate decisions
            results = []
            for decision in decisions:
                # Calculate weighted score
                total_score = 0.0
                for criterion, weight in zip(self._criteria, self._weights):
                    score = await criterion.evaluate(decision, context, messages)
                    total_score += score * weight
                    
                # Update confidence
                decision.confidence *= total_score
                
                # Add if meets minimum score
                if total_score >= self._min_score:
                    results.append(decision)
                    
            return results
            
        except Exception as e:
            raise CriteriaError(f"Failed to evaluate decisions: {e}") from e
            
    def _normalize_weights(self, weights: List[float]) -> List[float]:
        """Normalize weights to sum to 1.
        
        Args:
            weights: Weights to normalize
            
        Returns:
            Normalized weights
            
        Raises:
            ValueError: If weights are invalid
        """
        if len(weights) != len(self._criteria):
            raise ValueError(
                f"Expected {len(self._criteria)} weights, got {len(weights)}"
            )
            
        if not all(w >= 0 for w in weights):
            raise ValueError("Weights must be non-negative")
            
        total = sum(weights)
        if total <= 0:
            raise ValueError("Total weight must be positive")
            
        return [w / total for w in weights]
        
    def validate(self) -> None:
        """Validate evaluator state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Evaluator name cannot be empty")
            
        if not self._criteria:
            raise ValueError("No evaluation criteria provided")
            
        if not all(0 <= w <= 1 for w in self._weights):
            raise ValueError("Weights must be between 0 and 1")
            
        if not 0 <= self._min_score <= 1:
            raise ValueError("Minimum score must be between 0 and 1")
