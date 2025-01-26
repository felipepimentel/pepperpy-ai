"""Decision engine implementation."""
from typing import Any, Dict, List, Optional, Type

from .strategies import DecisionStrategy, SimpleStrategy, WeightedStrategy, ProbabilisticStrategy
from ..base.capability import BaseCapability

class RuleEvaluator:
    """Helper class for evaluating decision rules."""
    
    def evaluate_rule(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate if a rule matches the given context."""
        conditions = rule.get("conditions", {})
        return all(
            key in context and context[key] == value
            for key, value in conditions.items()
        )
    
    def matches_rule_outcome(self, rule: Dict[str, Any], option: Any) -> bool:
        """Check if option matches rule outcome."""
        outcome = rule.get("outcome", {})
        if not isinstance(option, dict):
            return True
        return all(
            key in option and option[key] == value
            for key, value in outcome.items()
        )
    
    def calculate_rule_score(
        self,
        rule: Dict[str, Any],
        option: Any,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate score for option based on rule."""
        if not isinstance(option, dict):
            return 0.0
            
        score = 0.0
        outcome = rule.get("outcome", {})
        weights = weights or {}
        
        for key, value in outcome.items():
            if key in option and option[key] == value:
                score += weights.get(key, 1.0)
        return score

class DecisionEngine(BaseCapability):
    """Engine for making decisions based on context and rules."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the decision engine."""
        super().__init__(config)
        self.rules = config.get("rules", [])
        self.default_strategy = config.get("default_strategy", "simple")
        self._strategies = {
            "simple": SimpleStrategy,
            "weighted": WeightedStrategy,
            "probabilistic": ProbabilisticStrategy
        }
        self._active_strategies = {}
        self._rule_evaluator = RuleEvaluator()
    
    async def initialize(self) -> None:
        """Initialize the decision engine."""
        if not self._initialized:
            await self._initialize_strategies()
            self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self._active_strategies.clear()
        self._initialized = False
    
    async def _initialize_strategies(self) -> None:
        """Initialize decision strategies."""
        for name, strategy_cls in self._strategies.items():
            self._active_strategies[name] = strategy_cls(self)
    
    async def decide(
        self,
        context: Dict[str, Any],
        options: List[Any],
        strategy: Optional[str] = None
    ) -> Any:
        """Make a decision based on context and available options."""
        if not self._initialized:
            raise RuntimeError("Engine not initialized")
        
        if not options:
            return None
        
        strategy_name = strategy or self.default_strategy
        if strategy_name not in self._active_strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
            
        return await self._active_strategies[strategy_name].decide(context, options)
    
    def get_rule_evaluator(self) -> RuleEvaluator:
        """Get the rule evaluator instance."""
        return self._rule_evaluator 