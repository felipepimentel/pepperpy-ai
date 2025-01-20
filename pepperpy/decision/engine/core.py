"""Core decision engine implementation."""

import logging
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ...common.errors import PepperpyError
from ...core.lifecycle import Lifecycle
from ...models.types import Message


logger = logging.getLogger(__name__)


class DecisionError(PepperpyError):
    """Decision error."""
    pass


class Decision:
    """Decision representation."""
    
    def __init__(
        self,
        action: str,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize decision.
        
        Args:
            action: Action to take
            confidence: Confidence score (0-1)
            metadata: Optional decision metadata
        """
        self.action = action
        self.confidence = confidence
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary.
        
        Returns:
            Decision as dictionary
        """
        return {
            "action": self.action,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Decision":
        """Create decision from dictionary.
        
        Args:
            data: Decision data
            
        Returns:
            Decision instance
        """
        return cls(
            action=data["action"],
            confidence=data["confidence"],
            metadata=data.get("metadata"),
        )


class Policy(Protocol):
    """Decision policy protocol."""
    
    async def evaluate(
        self,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> List[Decision]:
        """Evaluate context and messages to generate decisions.
        
        Args:
            context: Decision context
            messages: Input messages
            
        Returns:
            List of decisions
            
        Raises:
            DecisionError: If decisions cannot be generated
        """
        ...


P = TypeVar("P", bound=Policy)


class DecisionEngine(Lifecycle):
    """Decision engine implementation."""
    
    def __init__(
        self,
        name: str,
        policy: Policy,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize decision engine.
        
        Args:
            name: Engine name
            policy: Decision policy
            config: Optional engine configuration
        """
        super().__init__(name)
        self._policy = policy
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return engine configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize engine."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up engine."""
        pass
        
    async def decide(
        self,
        context: Dict[str, Any],
        messages: List[Message],
    ) -> List[Decision]:
        """Generate decisions from context and messages.
        
        Args:
            context: Decision context
            messages: Input messages
            
        Returns:
            List of decisions
            
        Raises:
            DecisionError: If decisions cannot be generated
        """
        try:
            return await self._policy.evaluate(context, messages)
            
        except Exception as e:
            raise DecisionError(f"Failed to generate decisions: {e}") from e
            
    def validate(self) -> None:
        """Validate engine state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Engine name cannot be empty")
            
        if not self._policy:
            raise ValueError("Decision policy not provided")
