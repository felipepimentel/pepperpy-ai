"""Agent Intent Module.

This module provides intent recognition capabilities for agents,
including intent classification, parameter extraction, and confidence scoring.

Example:
    >>> from pepperpy.agent.internal.intent import Intent
    >>> intent = Intent(
    ...     name="get_weather",
    ...     confidence=0.95,
    ...     parameters={"location": "London"}
    ... )
    >>> assert intent.name == "get_weather"
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from pepperpy.core.intent import Intent as CoreIntent
from pepperpy.core.validation import ValidationError


@dataclass
class Intent(CoreIntent):
    """Recognized intent from user input.

    This class extends the core Intent class with additional functionality
    specific to agent interactions, including metadata and validation.

    Args:
        name: Intent name
        confidence: Confidence score (0-1)
        parameters: Extracted parameters
        metadata: Additional intent metadata

    Example:
        >>> intent = Intent(
        ...     name="get_weather",
        ...     confidence=0.95,
        ...     parameters={"location": "London"}
        ... )
        >>> print(intent.name)
        get_weather
        >>> print(intent.parameters["location"])
        London
    """

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate intent after initialization.

        Raises:
            ValidationError: If confidence is not between 0 and 1
        """
        if not 0 <= self.confidence <= 1:
            raise ValidationError(
                "Confidence must be between 0 and 1",
                field="confidence",
                rule="range",
            )

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get a parameter value by name.

        Args:
            name: Parameter name
            default: Default value if parameter not found

        Returns:
            Parameter value or default

        Example:
            >>> intent = Intent(
            ...     "get_weather",
            ...     0.9,
            ...     parameters={"city": "London"}
            ... )
            >>> city = intent.get_parameter("city", "Unknown")
            >>> assert city == "London"
        """
        return self.parameters.get(name, default)

    def update_confidence(self, new_confidence: float) -> None:
        """Update intent confidence score.

        Args:
            new_confidence: New confidence score (0-1)

        Raises:
            ValidationError: If new_confidence is not between 0 and 1

        Example:
            >>> intent = Intent("get_weather", 0.8)
            >>> intent.update_confidence(0.95)
            >>> assert intent.confidence == 0.95
        """
        if not 0 <= new_confidence <= 1:
            raise ValidationError(
                "Confidence must be between 0 and 1",
                field="confidence",
                rule="range",
            )
        self.confidence = new_confidence

    def merge_parameters(self, other: "Intent") -> None:
        """Merge parameters from another intent.

        This method updates the current intent's parameters with
        parameters from another intent, preserving existing values
        unless overwritten.

        Args:
            other: Intent to merge parameters from

        Example:
            >>> intent1 = Intent(
            ...     "get_weather",
            ...     0.9,
            ...     parameters={"city": "London"}
            ... )
            >>> intent2 = Intent(
            ...     "get_weather",
            ...     0.8,
            ...     parameters={"country": "UK"}
            ... )
            >>> intent1.merge_parameters(intent2)
            >>> assert intent1.parameters == {
            ...     "city": "London",
            ...     "country": "UK"
            ... }
        """
        self.parameters.update(other.parameters)

    def matches(self, pattern: str, threshold: Optional[float] = None) -> bool:
        """Check if intent matches a pattern.

        Args:
            pattern: Intent name pattern to match
            threshold: Optional confidence threshold (0-1)

        Returns:
            True if intent matches pattern and confidence threshold

        Example:
            >>> intent = Intent("get_weather", 0.9)
            >>> assert intent.matches("get_*", 0.8)
            >>> assert not intent.matches("set_*")
        """
        if threshold is not None and self.confidence < threshold:
            return False

        # Convert pattern to regex-like matching
        pattern = pattern.replace("*", ".*")
        return bool(__import__("re").match(pattern, self.name))
