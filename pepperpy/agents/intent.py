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

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pepperpy.cache import cached
from pepperpy.core.intent import Intent as CoreIntent
from pepperpy.core.logging import get_logger
from pepperpy.core.validation import ValidationError

logger = get_logger(__name__)

# Enhanced intent patterns with parameter extraction
INTENT_PATTERNS = [
    # Question intents
    (r"\b(what|who|when|where|how|why|which)\b.*\?", "question", {"subject": r"about\s+(.+?)(?:\s+in|\s+for|\?|$)"}),
    (r"\bdefine\b|\bmeaning\b|\bwhat is\b", "definition", {"term": r"(?:is|of|the)\s+([^?.,]+)(?:\?|$)"}),
    # Creation intents
    (r"\bcreate\b|\bdevelop\b|\bgenerate\b|\bmake\b", "create", {"format": r"(?:an?|the)\s+(\w+)"}),
    (r"\bwrite\b|\bcompose\b|\bdraft\b", "write", {"format": r"(?:an?|the)\s+(\w+)"}),
    # Analysis intents
    (r"\banalyze\b|\bexamine\b|\bevaluate\b", "analyze", {"subject": r"(?:this|the)\s+([^.,?]+)"}),
    (r"\bcompare\b|\bdifference\b|\bsimilarity\b", "compare", {"items": r"between\s+(.+?)\s+and\s+(.+?)(?:\?|$)"}),
    # Processing intents
    (r"\bprocess\b|\btransform\b|\bconvert\b", "process", {"format": r"(?:to|into|as)\s+(?:an?|the)\s+(\w+)"}),
    (r"\bsummarize\b|\bsynthesis\b", "summarize", {"length": r"in\s+(\d+)\s+(?:words|sentences|paragraphs)"}),
    # Configuration intents
    (r"\bconfigure\b|\badjust\b|\bset\s+config", "configure", {"setting": r"(?:the|for)\s+(\w+)"}),
]

# Enhanced keywords for each intent type
INTENT_KEYWORDS = {
    "question": [
        "question", "explain", "answer", "clarify", "help", "tell me",
        "what", "who", "when", "where", "how", "why", "which"
    ],
    "analyze": [
        "analysis", "analyze", "examine", "investigate", "explain", "interpret",
        "evaluate", "assess", "review", "check", "inspect", "study"
    ],
    "create": [
        "create", "generate", "produce", "develop", "build", "implement",
        "design", "construct", "make", "craft", "form", "compose"
    ],
    "process": [
        "process", "transform", "convert", "modify", "adapt", "change",
        "translate", "rewrite", "rephrase", "alter", "update"
    ],
    "summarize": [
        "summarize", "synthesize", "condense", "abbreviate", "shorten",
        "brief", "digest", "synopsis", "outline", "recap"
    ],
    "compare": [
        "compare", "contrast", "differentiate", "distinguish", "versus",
        "similarity", "difference", "distinction", "relationship"
    ],
    "search": [
        "search", "find", "locate", "discover", "lookup", "seek",
        "query", "retrieve", "get", "fetch"
    ],
    "configure": [
        "configure", "setup", "set", "adjust", "tune", "customize",
        "preferences", "settings", "options", "parameters"
    ],
}

# Advanced parameter extraction patterns
PARAMETER_EXTRACTORS = {
    "language": r"(?:in|to)\s+(English|Spanish|French|German|Portuguese|Italian|Chinese|Japanese|Russian)",
    "count": r"(?:top|first|last)\s+(\d+)",
    "date": r"(?:on|from|until|before|after)\s+(\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})",
    "location": r"(?:in|at|from|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    "format": r"(?:as|in|to|into)\s+(?:an?|the)?\s+(pdf|json|csv|html|markdown|text|image|video|audio)",
    "length": r"(?:in|within)\s+(\d+)\s+(?:words|characters|sentences|paragraphs|pages)",
    "model": r"(?:using|with)\s+(gpt-4|gpt-3.5-turbo|claude|llama|palm|gemini)",
}


class IntentCategory(Enum):
    """Categories of intents for grouping similar intent types."""
    
    QUESTION = "question"
    CREATION = "creation"
    ANALYSIS = "analysis"
    PROCESSING = "processing"
    CONFIGURATION = "configuration"
    SEARCH = "search"
    ACTION = "action"
    UNKNOWN = "unknown"


INTENT_CATEGORIES = {
    "question": IntentCategory.QUESTION,
    "definition": IntentCategory.QUESTION,
    "create": IntentCategory.CREATION,
    "write": IntentCategory.CREATION,
    "generate": IntentCategory.CREATION,
    "analyze": IntentCategory.ANALYSIS,
    "compare": IntentCategory.ANALYSIS,
    "evaluate": IntentCategory.ANALYSIS,
    "process": IntentCategory.PROCESSING,
    "transform": IntentCategory.PROCESSING,
    "convert": IntentCategory.PROCESSING,
    "summarize": IntentCategory.PROCESSING,
    "configure": IntentCategory.CONFIGURATION,
    "setup": IntentCategory.CONFIGURATION,
    "search": IntentCategory.SEARCH,
    "find": IntentCategory.SEARCH,
}


@cached(ttl=3600, namespace="intent_analysis")
def analyze_intent(query: str) -> Tuple[str, Dict[str, Any], float]:
    """Analyze user query to determine the intent type, extract parameters, and assign confidence.
    
    This enhanced function examines query text and attempts to classify it into
    a known intent type, extract relevant parameters, and assign a confidence score.
    
    Args:
        query: The query to analyze
        
    Returns:
        A tuple of (intent_type, parameters, confidence)
        
    Example:
        >>> intent_type, params, confidence = analyze_intent("Analyze this PDF document")
        >>> print(intent_type)
        analyze
        >>> print(confidence)
        0.85
    """
    if not query or not isinstance(query, str):
        logger.warning(f"Invalid query for intent analysis: {query}")
        return "general", {}, 0.5
        
    # Convert to lowercase for easier matching
    query_lower = query.lower()
    
    # Initialize variables
    detected_intents: List[Tuple[str, float, Dict[str, Any]]] = []
    parameters: Dict[str, Any] = {}
    
    # Pattern-based analysis (high confidence)
    for pattern, intent_type, param_patterns in INTENT_PATTERNS:
        if re.search(pattern, query_lower):
            # Extract parameters if available
            intent_params = {}
            for param_name, param_pattern in param_patterns.items():
                match = re.search(param_pattern, query_lower)
                if match:
                    # Store all capture groups
                    if len(match.groups()) == 1:
                        intent_params[param_name] = match.group(1)
                    else:
                        for i, group in enumerate(match.groups(), 1):
                            if group:
                                intent_params[f"{param_name}_{i}" if i > 1 else param_name] = group
            
            # Add to detected intents with high confidence
            detected_intents.append((intent_type, 0.9, intent_params))
    
    # Keyword-based analysis (medium confidence)
    keyword_scores: Dict[str, float] = {}
    for intent_type, keywords in INTENT_KEYWORDS.items():
        score = 0.0
        matches = 0
        
        for keyword in keywords:
            if f" {keyword} " in f" {query_lower} ":
                matches += 1
                # Keywords at the beginning get higher weight
                position_factor = 1.0
                if query_lower.startswith(keyword):
                    position_factor = 1.5
                
                # Add to score, considering position
                score += 0.1 * position_factor
        
        if matches > 0:
            keyword_scores[intent_type] = min(0.8, score) # Cap at 0.8
    
    # Add keyword-based intents
    for intent_type, score in keyword_scores.items():
        if score >= 0.3:  # Only add if reasonable confidence
            detected_intents.append((intent_type, score, {}))
    
    # Extract generic parameters using patterns
    for param_name, param_pattern in PARAMETER_EXTRACTORS.items():
        match = re.search(param_pattern, query)
        if match:
            parameters[param_name] = match.group(1)
    
    # No intents detected
    if not detected_intents:
        # Try to use semantic understanding based on common question patterns
        if query_lower.endswith("?"):
            return "question", parameters, 0.7
        elif any(query_lower.startswith(w) for w in ["how", "what", "why", "when", "where", "who"]):
            return "question", parameters, 0.7
        else:
            return "general", parameters, 0.5
    
    # Sort by confidence and get the best match
    detected_intents.sort(key=lambda x: x[1], reverse=True)
    best_intent, confidence, intent_params = detected_intents[0]
    
    # Merge parameters
    parameters.update(intent_params)
    
    # Adjust confidence based on parameter extraction
    if parameters:
        confidence = min(0.95, confidence + 0.05 * len(parameters))
    
    logger.debug(f"Detected intent '{best_intent}' with confidence {confidence:.2f} for query: {query}")
    logger.debug(f"Extracted parameters: {parameters}")
    
    return best_intent, parameters, confidence


# Remover ou comentar a função create_intent_from_query que está causando problemas
'''
def create_intent_from_query(query: str) -> Intent:
    """Create an Intent object from a user query.
    
    Args:
        query: The user query to analyze
        
    Returns:
        Intent object with detected intent, parameters, and confidence
        
    Example:
        >>> intent = create_intent_from_query("What's the weather in London?")
        >>> print(intent.name)
        question
        >>> print(intent.parameters.get("location"))
        London
    """
    intent_type, parameters, confidence = analyze_intent(query)
    
    # Set appropriate category
    category = INTENT_CATEGORIES.get(intent_type, IntentCategory.UNKNOWN)
    
    # Use the constructor directly passing all parameters
    return Intent(
        intent_type,
        confidence,
        parameters,
        {"category": category.value, "query": query}
    )
'''


@dataclass
class Intent(CoreIntent):
    """Recognized intent from user input.
    
    This enhanced class extends the core Intent class with additional functionality
    specific to agent interactions, including advanced metadata, parameter validation,
    and intent comparison.
    
    Args:
        name: Intent name
        confidence: Confidence score (0-1)
        parameters: Extracted parameters
        metadata: Additional intent metadata
        
    Example:
        >>> intent = Intent(
        ...     "get_weather",
        ...     0.95,
        ...     parameters={"location": "London"}
        ... )
        >>> print(intent.name)
        get_weather
        >>> print(intent.parameters["location"])
        London
    """
    
    # Only add the new fields, as the base class handles the others
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
        return bool(re.match(pattern, self.name))
    
    def get_category(self) -> IntentCategory:
        """Get the category of this intent.
        
        Returns:
            The intent category enum value
            
        Example:
            >>> intent = Intent("question", 0.9)
            >>> assert intent.get_category() == IntentCategory.QUESTION
        """
        if "category" in self.metadata:
            # Try to get from metadata first
            try:
                return IntentCategory(self.metadata["category"])
            except ValueError:
                pass
                
        # Fall back to lookup
        return INTENT_CATEGORIES.get(self.name, IntentCategory.UNKNOWN)
    
    def requires_parameters(self, *param_names: str) -> bool:
        """Check if intent has all required parameters.
        
        Args:
            *param_names: Names of required parameters
            
        Returns:
            True if all required parameters are present
            
        Example:
            >>> intent = Intent(
            ...     "get_weather", 
            ...     0.9, 
            ...     parameters={"city": "London", "date": "today"}
            ... )
            >>> assert intent.requires_parameters("city")
            >>> assert intent.requires_parameters("city", "date")
            >>> assert not intent.requires_parameters("city", "country")
        """
        return all(param in self.parameters for param in param_names)
    
    def is_similar_to(self, other: "Intent", threshold: float = 0.5) -> bool:
        """Check if this intent is similar to another intent.
        
        Compares names, categories, and parameters to determine similarity.
        
        Args:
            other: Intent to compare with
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if intents are similar
        """
        # Same name is an automatic match
        if self.name == other.name:
            return True
            
        # Check category
        if self.get_category() == other.get_category():
            # Same category gives 0.6 similarity
            similarity = 0.6
            
            # Parameter overlap increases similarity
            if self.parameters and other.parameters:
                common_params = set(self.parameters.keys()) & set(other.parameters.keys())
                param_similarity = len(common_params) / max(len(self.parameters), len(other.parameters))
                similarity += 0.4 * param_similarity
                
            return similarity >= threshold
            
        return False


def extract_user_intent(query: str) -> Dict[str, Any]:
    """Extract comprehensive intent information from a user query.

    This function combines intent detection, parameter extraction,
    and generates a rich intent object for agents.

    Args:
        query: The user query

    Returns:
        Dict with complete intent information
    """
    intent_type, parameters, confidence = analyze_intent(query)
    
    # Set appropriate category
    category = INTENT_CATEGORIES.get(intent_type, IntentCategory.UNKNOWN)
    
    return {
        "intent": intent_type,
        "confidence": confidence,
        "parameters": parameters,
        "category": category.value,
        "query": query,
    }
