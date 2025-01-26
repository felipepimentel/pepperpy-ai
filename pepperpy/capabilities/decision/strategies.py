"""Decision strategies implementation."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, cast

from ..base.capability import BaseCapability
from .engine import DecisionEngine

T = TypeVar('T', bound=BaseCapability)

class ScoreCalculator:
    """Helper class for calculating scores."""
    
    def __init__(self, rule_evaluator: Any, rules: List[Dict[str, Any]]):
        """Initialize score calculator."""
        self.rule_evaluator = rule_evaluator
        self.rules = rules
    
    def calculate_score(
        self,
        option: Any,
        context: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate score for option."""
        if not isinstance(option, dict):
            return 0.0 if weights else 1.0
            
        score = 0.0
        for rule in self.rules:
            if self.rule_evaluator.evaluate_rule(rule, context):
                score += self.rule_evaluator.calculate_rule_score(
                    rule, option, weights
                )
        return score

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
        if not options:
            return None
            
        # Find first option with non-zero score
        for option in options:
            if self.score_calculator.calculate_score(option, context) > 0:
                return option
                
        return options[0]

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
        if not options:
            return None
            
        scores = {
            option: self.score_calculator.calculate_score(
                option, context, self.weights
            )
            for option in options
        }
        return max(scores.items(), key=lambda x: x[1])[0]

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
            self.score_calculator.calculate_score(option, context) + 1.0
            for option in options
        ]
        
        # Apply temperature and normalize
        if self.temperature != 0:
            scores = [s / self.temperature for s in scores]
            
        total = sum(scores)
        if total == 0:
            return options[0]
            
        # Sample based on probabilities
        import random
        r = random.random() * total
        cumsum = 0
        for option, score in zip(options, scores):
            cumsum += score
            if r <= cumsum:
                return option
                
        return options[-1] 