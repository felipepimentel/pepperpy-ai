"""Utilitários para manipulação de strings (DEPRECATED).

Implementa funções auxiliares para manipulação e formatação de strings.

This module is deprecated and will be removed in version 1.0.0.
Please use 'pepperpy.core.utils.collections.StringUtils' instead.
"""

import re
import warnings
from typing import List, Optional

# Show deprecation warning
warnings.warn(
    "The 'pepperpy.core.utils.strings' module is deprecated and will be removed in version 1.0.0. "
    "Please use 'pepperpy.core.utils.collections.StringUtils' instead.",
    DeprecationWarning,
    stacklevel=2,
)


class StringUtils:
    """Utility functions for string manipulation."""

    @staticmethod
    def is_empty(text: Optional[str]) -> bool:
        """Check if string is empty.

        Args:
            text: String to check

        Returns:
            True if string is None or empty
        """
        return text is None or text.strip() == ""

    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate string to maximum length.

        Args:
            text: String to truncate
            max_length: Maximum length
            suffix: Suffix to append if truncated

        Returns:
            Truncated string
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - len(suffix)] + suffix

    @staticmethod
    def slugify(text: str) -> str:
        """Convert string to slug format.

        Args:
            text: String to convert

        Returns:
            Slug string
        """
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        return text.strip("-")

    @staticmethod
    def camel_to_snake(text: str) -> str:
        """Convert camelCase to snake_case.

        Args:
            text: String to convert

        Returns:
            snake_case string
        """
        pattern = re.compile(r"(?<!^)(?=[A-Z])")
        return pattern.sub("_", text).lower()

    @staticmethod
    def snake_to_camel(text: str) -> str:
        """Convert snake_case to camelCase.

        Args:
            text: String to convert

        Returns:
            camelCase string
        """
        components = text.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    @staticmethod
    def split_words(text: str) -> List[str]:
        """Split string into words.

        Args:
            text: String to split

        Returns:
            List of words
        """
        return [w for w in re.split(r"\W+", text) if w]

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in string.

        Args:
            text: String to normalize

        Returns:
            Normalized string
        """
        return " ".join(text.split())

    @staticmethod
    def remove_accents(text: str) -> str:
        """Remove accents from string.

        Args:
            text: String to process

        Returns:
            String without accents
        """
        import unicodedata

        return "".join(
            c
            for c in unicodedata.normalize("NFKD", text)
            if not unicodedata.combining(c)
        )

    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """Extract numbers from string.

        Args:
            text: String to process

        Returns:
            List of numbers
        """
        return re.findall(r"\d+", text)

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from string.

        Args:
            text: String to process

        Returns:
            List of email addresses
        """
        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return re.findall(pattern, text)

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from string.

        Args:
            text: String to process

        Returns:
            List of URLs
        """
        pattern = (
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|"
            r"[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        return re.findall(pattern, text)
