"""Intent handling for PepperPy.
 
This module provides intent handling functionality.
"""


from typing import Any, Dict, Optional


class Intent:
    """Intent class.

    This class represents an intent with its parameters and confidence.
    """

    def __init__(
        self,
        name: str,
        confidence: float = 0.0,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the intent.

        Args:
            name: Name of the intent
            confidence: Confidence score
            parameters: Optional parameters
        """
        self.name = name
        self.confidence = confidence
        self.parameters = parameters or {}

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            String representation of the intent
        """
        return (
            f"Intent(name={self.name}, "
            f"confidence={self.confidence}, "
            f"parameters={self.parameters})"
        )


class IntentBuilder:
    """Intent builder class.

    This class provides a fluent interface for building intents.
    """

    def __init__(self, name: str):
        """Initialize the intent builder.

        Args:
            name: Name of the intent
        """
        self._name = name
        self._confidence = 0.0
        self._parameters: Dict[str, Any] = {}

    def with_confidence(self, confidence: float) -> "IntentBuilder":
        """Set the confidence score.

        Args:
            confidence: Confidence score

        Returns:
            Self for chaining
        """
        self._confidence = confidence
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

    def build(self) -> Intent:
        """Build the intent.

        Returns:
            Built intent
        """
        return Intent(
            name=self._name,
            confidence=self._confidence,
            parameters=self._parameters,
        )
