"""Decision policy implementations."""

import logging
from typing import Any, Dict, List, Optional, Protocol, Set

from ...common.errors import PepperpyError
from ...models.types import Message
from .core import Decision, DecisionError, Policy


logger = logging.getLogger(__name__)


class Rule(Protocol):
    """Decision rule protocol."""
    
    async def apply(
        self,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> Optional[Decision]:
        """Apply rule to context and messages.
        
        Args:
            context: Decision context
            messages: Input messages
            
        Returns:
            Decision if rule applies, None otherwise
            
        Raises:
            DecisionError: If rule cannot be applied
        """
        ...


class RuleBasedPolicy(Policy):
    """Rule-based decision policy."""
    
    def __init__(
        self,
        rules: List[Rule],
        min_confidence: float = 0.0,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize policy.
        
        Args:
            rules: Decision rules
            min_confidence: Minimum confidence score (default: 0.0)
            config: Optional policy configuration
        """
        self._rules = rules
        self._min_confidence = min_confidence
        self._config = config or {}
        
    async def evaluate(
        self,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> List[Decision]:
        """Evaluate context and messages using rules.
        
        Args:
            context: Decision context
            messages: Input messages
            
        Returns:
            List of decisions
            
        Raises:
            DecisionError: If decisions cannot be generated
        """
        try:
            # Apply rules
            decisions = []
            for rule in self._rules:
                decision = await rule.apply(context, messages)
                if decision and decision.confidence >= self._min_confidence:
                    decisions.append(decision)
                    
            return decisions
            
        except Exception as e:
            raise DecisionError(f"Failed to evaluate rules: {e}") from e


class PrioritizedPolicy(Policy):
    """Prioritized decision policy."""
    
    def __init__(
        self,
        policies: List[Policy],
        min_confidence: float = 0.0,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize policy.
        
        Args:
            policies: Decision policies in priority order
            min_confidence: Minimum confidence score (default: 0.0)
            config: Optional policy configuration
        """
        self._policies = policies
        self._min_confidence = min_confidence
        self._config = config or {}
        
    async def evaluate(
        self,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> List[Decision]:
        """Evaluate context and messages using prioritized policies.
        
        Args:
            context: Decision context
            messages: Input messages
            
        Returns:
            List of decisions
            
        Raises:
            DecisionError: If decisions cannot be generated
        """
        try:
            # Try policies in order
            for policy in self._policies:
                decisions = await policy.evaluate(context, messages)
                if decisions:
                    # Filter by confidence
                    decisions = [
                        d for d in decisions
                        if d.confidence >= self._min_confidence
                    ]
                    if decisions:
                        return decisions
                        
            return []
            
        except Exception as e:
            raise DecisionError(f"Failed to evaluate policies: {e}") from e


class CompositePolicy(Policy):
    """Composite decision policy."""
    
    def __init__(
        self,
        policies: List[Policy],
        min_confidence: float = 0.0,
        unique_actions: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize policy.
        
        Args:
            policies: Decision policies to combine
            min_confidence: Minimum confidence score (default: 0.0)
            unique_actions: Whether to enforce unique actions (default: True)
            config: Optional policy configuration
        """
        self._policies = policies
        self._min_confidence = min_confidence
        self._unique_actions = unique_actions
        self._config = config or {}
        
    async def evaluate(
        self,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> List[Decision]:
        """Evaluate context and messages using all policies.
        
        Args:
            context: Decision context
            messages: Input messages
            
        Returns:
            List of decisions
            
        Raises:
            DecisionError: If decisions cannot be generated
        """
        try:
            # Evaluate all policies
            all_decisions = []
            seen_actions: Set[str] = set()
            
            for policy in self._policies:
                decisions = await policy.evaluate(context, messages)
                
                # Filter by confidence
                decisions = [
                    d for d in decisions
                    if d.confidence >= self._min_confidence
                ]
                
                # Filter unique actions
                if self._unique_actions:
                    decisions = [
                        d for d in decisions
                        if d.action not in seen_actions
                    ]
                    seen_actions.update(d.action for d in decisions)
                    
                all_decisions.extend(decisions)
                
            return all_decisions
            
        except Exception as e:
            raise DecisionError(f"Failed to evaluate policies: {e}") from e
