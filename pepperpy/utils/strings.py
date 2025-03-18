"""String utilities for the PepperPy framework.

This module provides utility functions for string manipulation and processing.
"""

import re
import unicodedata
from typing import List, Optional, Pattern, Set, Tuple


def slugify(text: str, separator: str = "-") -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: The text to convert
        separator: The separator to use between words

    Returns:
        A URL-friendly slug
    """
    # Convert to lowercase and normalize unicode characters
    text = unicodedata.normalize("NFKD", text.lower())

    # Remove non-alphanumeric characters
    text = re.sub(r"[^\w\s-]", "", text).strip()

    # Replace whitespace with separator
    text = re.sub(r"[\s_-]+", separator, text)

    return text


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        text: The text to truncate
        max_length: The maximum length of the truncated text
        suffix: The suffix to append to truncated text

    Returns:
        The truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def extract_keywords(
    text: str, min_length: int = 3, max_keywords: Optional[int] = None
) -> List[str]:
    """Extract keywords from text.

    Args:
        text: The text to extract keywords from
        min_length: The minimum length of keywords
        max_keywords: The maximum number of keywords to return

    Returns:
        A list of keywords
    """
    # Convert to lowercase and remove punctuation
    text = re.sub(r"[^\w\s]", "", text.lower())

    # Split into words
    words = text.split()

    # Filter out short words and common stop words
    stop_words = {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "if",
        "then",
        "else",
        "when",
        "at",
        "from",
        "by",
        "for",
        "with",
        "about",
        "against",
        "between",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "to",
        "of",
        "in",
        "on",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        "can",
        "could",
        "should",
        "would",
        "may",
        "might",
        "must",
        "will",
    }

    keywords = [
        word for word in words if len(word) >= min_length and word not in stop_words
    ]

    # Remove duplicates while preserving order
    seen: Set[str] = set()
    unique_keywords = [kw for kw in keywords if not (kw in seen or seen.add(kw))]

    # Limit the number of keywords
    if max_keywords is not None:
        unique_keywords = unique_keywords[:max_keywords]

    return unique_keywords


def find_all(text: str, pattern: str) -> List[Tuple[int, int]]:
    """Find all occurrences of a pattern in text.

    Args:
        text: The text to search in
        pattern: The pattern to search for

    Returns:
        A list of (start, end) tuples for each match
    """
    compiled_pattern: Pattern = re.compile(pattern)
    return [(match.start(), match.end()) for match in compiled_pattern.finditer(text)]


def replace_placeholders(template: str, replacements: dict) -> str:
    """Replace placeholders in a template string.

    Args:
        template: The template string with {placeholder} syntax
        replacements: A dictionary of placeholder -> replacement mappings

    Returns:
        The template with placeholders replaced
    """
    return template.format(**replacements)


def camel_to_snake(text: str) -> str:
    """Convert camelCase to snake_case.

    Args:
        text: The camelCase text to convert

    Returns:
        The text in snake_case
    """
    # Insert underscore before uppercase letters and convert to lowercase
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", text)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_camel(text: str) -> str:
    """Convert snake_case to camelCase.

    Args:
        text: The snake_case text to convert

    Returns:
        The text in camelCase
    """
    # Split by underscore and capitalize each word except the first
    components = text.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def snake_to_pascal(text: str) -> str:
    """Convert snake_case to PascalCase.

    Args:
        text: The snake_case text to convert

    Returns:
        The text in PascalCase
    """
    # Split by underscore and capitalize each word
    return "".join(x.title() for x in text.split("_"))


def pascal_to_snake(text: str) -> str:
    """Convert PascalCase to snake_case.

    Args:
        text: The PascalCase text to convert

    Returns:
        The text in snake_case
    """
    # Same as camel_to_snake
    return camel_to_snake(text)


__all__ = [
    "slugify",
    "truncate",
    "extract_keywords",
    "find_all",
    "replace_placeholders",
    "camel_to_snake",
    "snake_to_camel",
    "snake_to_pascal",
    "pascal_to_snake",
]
