"""Decision criteria rules implementation."""

import logging
from typing import Any, Dict, List, Optional, Protocol, Set, TypeVar

from ...common.errors import PepperpyError
from ...models.types import Message
from ..engine.core import Decision
from .evaluator import Criterion, CriteriaError


logger = logging.getLogger(__name__)


class RuleError(PepperpyError):
    """Rule error."""
    pass


class Rule(Protocol):
    """Decision rule protocol."""
    
    async def apply(
        self,
        decision: Decision,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> bool:
        """Apply rule to decision.
        
        Args:
            decision: Decision to evaluate
            context: Decision context
            messages: Input messages
            
        Returns:
            True if rule passes, False otherwise
            
        Raises:
            RuleError: If rule cannot be applied
        """
        ...


R = TypeVar("R", bound=Rule)


class RuleCriterion(Criterion):
    """Rule-based decision criterion."""
    
    def __init__(
        self,
        rules: List[Rule],
        weights: Optional[List[float]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize criterion.
        
        Args:
            rules: Decision rules
            weights: Optional rule weights (default: equal weights)
            config: Optional criterion configuration
        """
        self._rules = rules
        self._weights = self._normalize_weights(weights or [1.0] * len(rules))
        self._config = config or {}
        
    async def evaluate(
        self,
        decision: Decision,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> float:
        """Evaluate decision against rules.
        
        Args:
            decision: Decision to evaluate
            context: Decision context
            messages: Input messages
            
        Returns:
            Score between 0 and 1
            
        Raises:
            CriteriaError: If criterion cannot be evaluated
        """
        try:
            # Apply rules
            total_score = 0.0
            for rule, weight in zip(self._rules, self._weights):
                if await rule.apply(decision, context, messages):
                    total_score += weight
                    
            return total_score
            
        except Exception as e:
            raise CriteriaError(f"Failed to evaluate rules: {e}") from e
            
    def _normalize_weights(self, weights: List[float]) -> List[float]:
        """Normalize weights to sum to 1.
        
        Args:
            weights: Weights to normalize
            
        Returns:
            Normalized weights
            
        Raises:
            ValueError: If weights are invalid
        """
        if len(weights) != len(self._rules):
            raise ValueError(
                f"Expected {len(self._rules)} weights, got {len(weights)}"
            )
            
        if not all(w >= 0 for w in weights):
            raise ValueError("Weights must be non-negative")
            
        total = sum(weights)
        if total <= 0:
            raise ValueError("Total weight must be positive")
            
        return [w / total for w in weights]


class ActionRule(Rule):
    """Action-based decision rule."""
    
    def __init__(
        self,
        allowed_actions: Optional[Set[str]] = None,
        blocked_actions: Optional[Set[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize rule.
        
        Args:
            allowed_actions: Optional set of allowed actions
            blocked_actions: Optional set of blocked actions
            config: Optional rule configuration
        """
        self._allowed_actions = allowed_actions
        self._blocked_actions = blocked_actions or set()
        self._config = config or {}
        
    async def apply(
        self,
        decision: Decision,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> bool:
        """Apply rule to decision.
        
        Args:
            decision: Decision to evaluate
            context: Decision context
            messages: Input messages
            
        Returns:
            True if action is allowed, False otherwise
            
        Raises:
            RuleError: If rule cannot be applied
        """
        try:
            # Check if action is blocked
            if decision.action in self._blocked_actions:
                return False
                
            # Check if action is allowed
            if self._allowed_actions is not None:
                return decision.action in self._allowed_actions
                
            return True
            
        except Exception as e:
            raise RuleError(f"Failed to apply rule: {e}") from e


class ConfidenceRule(Rule):
    """Confidence-based decision rule."""
    
    def __init__(
        self,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize rule.
        
        Args:
            min_confidence: Minimum confidence score (default: 0.0)
            max_confidence: Maximum confidence score (default: 1.0)
            config: Optional rule configuration
        """
        self._min_confidence = min_confidence
        self._max_confidence = max_confidence
        self._config = config or {}
        
    async def apply(
        self,
        decision: Decision,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> bool:
        """Apply rule to decision.
        
        Args:
            decision: Decision to evaluate
            context: Decision context
            messages: Input messages
            
        Returns:
            True if confidence is within range, False otherwise
            
        Raises:
            RuleError: If rule cannot be applied
        """
        try:
            return (
                self._min_confidence <= decision.confidence <= self._max_confidence
            )
            
        except Exception as e:
            raise RuleError(f"Failed to apply rule: {e}") from e


class MetadataRule(Rule):
    """Metadata-based decision rule."""
    
    def __init__(
        self,
        required_keys: Optional[Set[str]] = None,
        blocked_keys: Optional[Set[str]] = None,
        required_values: Optional[Dict[str, Any]] = None,
        blocked_values: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize rule.
        
        Args:
            required_keys: Optional set of required metadata keys
            blocked_keys: Optional set of blocked metadata keys
            required_values: Optional dict of required metadata values
            blocked_values: Optional dict of blocked metadata values
            config: Optional rule configuration
        """
        self._required_keys = required_keys
        self._blocked_keys = blocked_keys or set()
        self._required_values = required_values or {}
        self._blocked_values = blocked_values or {}
        self._config = config or {}
        
    async def apply(
        self,
        decision: Decision,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> bool:
        """Apply rule to decision.
        
        Args:
            decision: Decision to evaluate
            context: Decision context
            messages: Input messages
            
        Returns:
            True if metadata meets requirements, False otherwise
            
        Raises:
            RuleError: If rule cannot be applied
        """
        try:
            # Check blocked keys
            if any(k in decision.metadata for k in self._blocked_keys):
                return False
                
            # Check required keys
            if self._required_keys is not None:
                if not all(k in decision.metadata for k in self._required_keys):
                    return False
                    
            # Check blocked values
            for key, value in self._blocked_values.items():
                if decision.metadata.get(key) == value:
                    return False
                    
            # Check required values
            for key, value in self._required_values.items():
                if decision.metadata.get(key) != value:
                    return False
                    
            return True
            
        except Exception as e:
            raise RuleError(f"Failed to apply rule: {e}") from e
