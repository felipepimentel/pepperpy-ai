"""Intent recognition and processing module.

This module provides functionality for recognizing and processing user intents
from natural language text. It supports basic intents like translation,
summarization, and search queries.

Example:
    >>> intent = await recognize_intent("traduzir hello world")
    >>> assert intent.name == "translate"
    >>> assert intent.entities["text"] == "hello world"
    >>> assert intent.confidence > 0.8

Note:
    This is a simplified implementation. For production use,
    consider using a more robust NLP solution.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class IntentType(str, Enum):
    """Type classification for intents.

    Attributes:
        QUERY: Intent represents a question or information request
        COMMAND: Intent represents an action to be performed
        CONVERSATION: Intent represents conversational dialogue

    Example:
        >>> intent_type = IntentType.QUERY
        >>> assert intent_type == "query"
        >>> assert IntentType("command") == IntentType.COMMAND
    """

    QUERY = "query"
    COMMAND = "command"
    CONVERSATION = "conversation"


@dataclass
class Intent:
    """Represents a recognized user intent.

    This class encapsulates the recognized intent from user input,
    including the intent name, type, confidence score, and any
    extracted entities.

    Attributes:
        name: The name of the recognized intent
        type: The type of intent (query, command, etc)
        confidence: Confidence score between 0 and 1
        entities: Dictionary of extracted entities

    Example:
        >>> intent = Intent(
        ...     name="translate",
        ...     type=IntentType.COMMAND,
        ...     confidence=0.95,
        ...     entities={"text": "hello world"}
        ... )
        >>> assert intent.name == "translate"
        >>> assert intent.confidence > 0.9
    """

    name: str
    type: IntentType
    confidence: float
    entities: Dict[str, Optional[str]]


async def recognize_intent(text: str) -> Intent:
    """Recognize intent from natural language text.

    This function analyzes the input text and extracts the user's
    intended action or query. It uses simple keyword matching for
    demonstration purposes.

    Args:
        text: The natural language text to analyze.
            Should be in Portuguese.

    Returns:
        Intent: The recognized intent with:
            - name: Intent identifier (e.g. "translate", "search")
            - type: Intent type classification
            - confidence: Recognition confidence (0-1)
            - entities: Extracted parameters

    Raises:
        ValueError: If the input text is empty or invalid.

    Example:
        >>> intent = await recognize_intent("traduzir hello world")
        >>> assert intent.name == "translate"
        >>> assert intent.entities["text"] == "hello world"
        >>> assert intent.confidence > 0.8

        >>> intent = await recognize_intent("resumir em http://example.com")
        >>> assert intent.name == "summarize"
        >>> assert intent.entities["url"] == "http://example.com"
    """
    if not text or not isinstance(text, str):
        raise ValueError("Input text must be a non-empty string")

    # Default values
    intent_type = IntentType.QUERY
    confidence = 0.85
    entities: Dict[str, Optional[str]] = {}

    # Recognize intent from text
    text_lower = text.lower()
    if "resumir" in text_lower:
        intent_name = "summarize"
        entities["url"] = text.split("em ")[-1] if "em " in text else None
    elif "traduzir" in text_lower:
        intent_name = "translate"
        entities["text"] = text.split("traduzir ")[-1] if "traduzir " in text else text
    elif "buscar" in text_lower or "pesquisar" in text_lower:
        intent_name = "search"
        entities["query"] = (
            text.split("buscar ")[-1]
            if "buscar " in text
            else text.split("pesquisar ")[-1]
            if "pesquisar " in text
            else text
        )
    else:
        intent_name = "unknown"
        confidence = 0.3

    return Intent(
        name=intent_name,
        type=intent_type,
        confidence=confidence,
        entities=entities,
    )
