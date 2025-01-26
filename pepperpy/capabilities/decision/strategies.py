"""Decision strategies implementation."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, cast

from ..base.capability import BaseCapability
from .engine import DecisionEngine
from .scoring import ScoreCalculator
from .utils import ProbabilityCalculator

T = TypeVar('T', bound=BaseCapability)

class DecisionStrategy(ABC):
    """Base class for decision strategies."""
    
    def __init__(self, capability: T):
        """Initialize the decision strategy."""
        self.capability = capability
        self.engine = cast(DecisionEngine, capability)
        self.rule_evaluator = self.engine.get_rule_evaluator()
        self.score_calculator = ScoreCalculator(
            self.rule_evaluator,
            self.engine.rules
        )
    
    @abstractmethod
    async def decide(
        self,
        context: Dict[str, Any],
        options: List[Any]
    ) -> Any:
        """Make a decision based on context and options."""
        pass

class SimpleStrategy(DecisionStrategy):
    """Simple strategy that returns first matching option."""
    
    async def decide(
        self,
        context: Dict[str, Any],
        options: List[Any]
    ) -> Any:
        """Return first option that matches context."""
        return self.score_calculator.find_first_match(options, context)

class WeightedStrategy(DecisionStrategy):
    """Strategy that weighs options based on context."""
    
    def __init__(
        self,
        capability: T,
        weights: Optional[Dict[str, float]] = None
    ):
        """Initialize the weighted strategy."""
        super().__init__(capability)
        self.weights = weights or {}
    
    async def decide(
        self,
        context: Dict[str, Any],
        options: List[Any]
    ) -> Any:
        """Return option with highest weighted score."""
        return self.score_calculator.find_highest_score(
            options,
            context,
            self.weights
        )

class ProbabilisticStrategy(DecisionStrategy):
    """Strategy that makes probabilistic decisions."""
    
    def __init__(
        self,
        capability: T,
        temperature: float = 1.0
    ):
        """Initialize the probabilistic strategy."""
        super().__init__(capability)
        self.temperature = temperature
        self.probability_calculator = ProbabilityCalculator()
    
    async def decide(
        self,
        context: Dict[str, Any],
        options: List[Any]
    ) -> Any:
        """Return option based on probabilistic sampling."""
        if not options:
            return None
            
        # Calculate base scores
        scores = [
            self.score_calculator.calculate_base_score(option, context) + 1.0
            for option in options
        ]
        
        # Sample based on probabilities
        return self.probability_calculator.sample(
            options,
            scores,
            self.temperature
        ) 