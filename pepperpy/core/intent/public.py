"""Public interface for intent module."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from pepperpy.core.base_manager import BaseManager
from pepperpy.core.base_registry import Registry  # type: ignore
from pepperpy.core.errors import PepperPyError
from pepperpy.providers.base import BaseProvider


@dataclass
class Intent:
    """Intent definition."""

    name: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntentBuilder:
    """Builder for intent objects."""

    def __init__(self, name: str):
        """Initialize the builder.

        Args:
            name: Intent name
        """
        self._name = name
        self._confidence = 1.0
        self._parameters: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}

    def with_confidence(self, confidence: float) -> "IntentBuilder":
        """Set the confidence score.

        Args:
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            Self for chaining
        """
        self._confidence = max(0.0, min(1.0, confidence))
        return self

    def with_parameter(self, name: str, value: Any) -> "IntentBuilder":
        """Add a parameter.

        Args:
            name: Parameter name
            value: Parameter value

        Returns:
            Self for chaining
        """
        self._parameters[name] = value
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> "IntentBuilder":
        """Add metadata.

        Args:
            metadata: Metadata to add

        Returns:
            Self for chaining
        """
        self._metadata.update(metadata)
        return self

    def build(self) -> Intent:
        """Build the intent.

        Returns:
            Built intent
        """
        return Intent(
            name=self._name,
            confidence=self._confidence,
            parameters=self._parameters,
            metadata=self._metadata,
        )


class IntentProvider(BaseProvider):
    """Base class for intent providers."""

    async def recognize(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Intent]:
        """Recognize intents in text.

        Args:
            text: Text to analyze
            metadata: Optional metadata

        Returns:
            List of recognized intents

        Raises:
            PepperpyError: If recognition fails
        """
        raise PepperPyError("Not implemented")

    async def train(
        self,
        examples: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Train the intent recognizer.

        Args:
            examples: Training examples
            metadata: Optional metadata

        Raises:
            PepperpyError: If training fails
        """
        raise PepperPyError("Not implemented")


class IntentManager(BaseManager[IntentProvider]):
    """Manager for intent recognition."""

    def __init__(self):
        """Initialize the manager."""
        registry = Registry[Type[IntentProvider]]("intent_registry", "intent")
        super().__init__("intent_manager", "intent", registry)

    async def recognize(
        self,
        text: str,
        provider_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Intent]:
        """Recognize intents in text.

        Args:
            text: Text to analyze
            provider_id: Optional provider to use
            metadata: Optional metadata

        Returns:
            List of recognized intents

        Raises:
            PepperpyError: If recognition fails
        """
        provider = await self.get_provider(provider_id)
        return await provider.recognize(text, metadata)

    async def train(
        self,
        examples: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Train the intent recognizer.

        Args:
            examples: Training examples
            provider_id: Optional provider to use
            metadata: Optional metadata

        Raises:
            PepperpyError: If training fails
        """
        provider = await self.get_provider(provider_id)
        await provider.train(examples, metadata)


async def process_intent(
    text: str,
    manager: Optional[IntentManager] = None,
    provider_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Intent]:
    """Process text to recognize intents.

    Args:
        text: Text to analyze
        manager: Optional intent manager to use
        provider_id: Optional provider to use
        metadata: Optional metadata

    Returns:
        List of recognized intents

    Raises:
        PepperpyError: If processing fails
    """
    try:
        # Create manager if not provided
        if manager is None:
            manager = IntentManager()

        # Recognize intents
        return await manager.recognize(text, provider_id, metadata)

    except Exception as e:
        raise PepperPyError(f"Error processing intent: {e}")


# Export all classes and functions
__all__ = [
    "Intent",
    "IntentBuilder",
    "IntentProvider",
    "IntentManager",
    "process_intent",
]
