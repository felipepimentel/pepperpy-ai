"""Text normalization abstractions for document processing.

This module provides abstract interfaces and base implementations for text normalization,
allowing concrete implementations to be provided by plugins.
"""

import logging
import re
import string
import unicodedata
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from pepperpy.core.base import PepperpyError

logger = logging.getLogger(__name__)


class TextNormalizationError(PepperpyError):
    """Error raised during text normalization operations."""

    pass


class TextNormalizer(ABC):
    """Abstract base text normalizer for document processing.

    This class provides the interface for text normalization implementations.
    Concrete normalizers should be implemented in plugins.
    """

    @abstractmethod
    def normalize(self, text: str) -> str:
        """Apply all configured normalizations to text.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        pass


class BaseTextNormalizer(TextNormalizer):
    """Basic text normalizer that provides common text transformations.

    This implementation handles basic text normalization without external dependencies.
    More advanced normalizers should be implemented in plugins.
    """

    # Default transformations to apply
    DEFAULT_TRANSFORMATIONS = [
        "strip_whitespace",
        "normalize_unicode",
        "normalize_whitespace",
        "remove_control_chars",
    ]

    # Default cleanup patterns
    DEFAULT_PATTERNS = {
        "url": r"https?://\S+|www\.\S+",
        "email": r"\S+@\S+\.\S+",
        "phone": r"\+?[\d\-\(\)\s]{7,}",
        "ssn": r"\d{3}-\d{2}-\d{4}",
        "credit_card": r"\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}",
        "ip_address": r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        "markdown_links": r"\[(.*?)\]\((.*?)\)",
        "html_tags": r"<[^>]*>",
        "extra_whitespace": r"\s+",
    }

    # Default replacements
    DEFAULT_REPLACEMENTS = {
        "\u201c": '"',  # Left double quotation mark
        "\u201d": '"',  # Right double quotation mark
        "\u2018": "'",  # Left single quotation mark
        "\u2019": "'",  # Right single quotation mark
        "\u2013": "-",  # En dash
        "\u2014": "--",  # Em dash
        "\u00a0": " ",  # Non-breaking space
        "\u00ad": "",  # Soft hyphen
        "\u00b7": "*",  # Middle dot
        "\u2022": "*",  # Bullet
        "\u2023": "*",  # Triangular bullet
        "\u2026": "...",  # Horizontal ellipsis
        "\u00ae": "(R)",  # Registered sign
        "\u00a9": "(C)",  # Copyright sign
        "\u2122": "TM",  # Trade mark sign
    }

    def __init__(
        self,
        transformations: Optional[List[str]] = None,
        custom_patterns: Optional[Dict[str, str]] = None,
        custom_replacements: Optional[Dict[str, str]] = None,
        language: str = "en",
        **kwargs: Any,
    ) -> None:
        """Initialize text normalizer.

        Args:
            transformations: List of transformation names to apply
            custom_patterns: Custom regex patterns for text cleaning
            custom_replacements: Custom character replacements
            language: Language code for language-specific processing
            **kwargs: Additional configuration options
        """
        # Set transformations
        self.transformations = transformations or self.DEFAULT_TRANSFORMATIONS

        # Set patterns
        self.patterns = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)

        # Compile patterns
        self.compiled_patterns = {
            name: re.compile(pattern) for name, pattern in self.patterns.items()
        }

        # Set replacements
        self.replacements = self.DEFAULT_REPLACEMENTS.copy()
        if custom_replacements:
            self.replacements.update(custom_replacements)

        # Set language
        self.language = language

    def normalize(self, text: str) -> str:
        """Apply all configured normalizations to text.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        if not text:
            return ""

        result = text

        # Apply transformations in order
        for transformation in self.transformations:
            transform_method = getattr(self, f"transform_{transformation}", None)
            if transform_method and callable(transform_method):
                result = transform_method(result)
            else:
                logger.warning(f"Unknown transformation: {transformation}")

        return result

    def transform_strip_whitespace(self, text: str) -> str:
        """Strip leading and trailing whitespace.

        Args:
            text: Input text

        Returns:
            Text with leading and trailing whitespace removed
        """
        return text.strip()

    def transform_normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters.

        Args:
            text: Input text

        Returns:
            Text with normalized Unicode
        """
        # Normalize to NFKC form (compatibility decomposition followed by canonical composition)
        return unicodedata.normalize("NFKC", text)

    def transform_normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace.

        Args:
            text: Input text

        Returns:
            Text with normalized whitespace
        """
        # Replace multiple whitespace with single space
        return re.sub(r"\s+", " ", text)

    def transform_remove_control_chars(self, text: str) -> str:
        """Remove control characters.

        Args:
            text: Input text

        Returns:
            Text with control characters removed
        """
        # Remove control characters except newlines and tabs
        return "".join(
            c
            for c in text
            if c == "\n" or c == "\t" or not unicodedata.category(c).startswith("C")
        )

    def transform_replace_chars(self, text: str) -> str:
        """Replace special characters with standard ones.

        Args:
            text: Input text

        Returns:
            Text with special characters replaced
        """
        # Replace special characters
        for old, new in self.replacements.items():
            text = text.replace(old, new)
        return text

    def transform_lowercase(self, text: str) -> str:
        """Convert text to lowercase.

        Args:
            text: Input text

        Returns:
            Lowercase text
        """
        return text.lower()

    def transform_remove_punctuation(self, text: str) -> str:
        """Remove punctuation.

        Args:
            text: Input text

        Returns:
            Text with punctuation removed
        """
        # Remove all punctuation
        return "".join(c for c in text if c not in string.punctuation)

    def transform_remove_numbers(self, text: str) -> str:
        """Remove numbers.

        Args:
            text: Input text

        Returns:
            Text with numbers removed
        """
        # Remove all digits
        return "".join(c for c in text if not c.isdigit())

    def transform_fix_encoding(self, text: str) -> str:
        """Fix common encoding issues.

        Args:
            text: Input text

        Returns:
            Text with encoding issues fixed
        """
        # Handle common encoding issues
        fixed = text

        # Replace common encoding artifacts - using simple replacements
        # Note: We're only handling a subset of common encoding issues with ASCII replacements
        fixed = fixed.replace("Â", " ")
        fixed = fixed.replace("'", "'")
        fixed = fixed.replace(
            """, '"')
        fixed = fixed.replace(""",
            '"',
        )
        fixed = fixed.replace("…", "...")
        fixed = fixed.replace("–", "-")  # En dash
        fixed = fixed.replace("—", "--")  # Em dash
        fixed = fixed.replace("é", "e")
        fixed = fixed.replace("è", "e")
        fixed = fixed.replace("à", "a")
        fixed = fixed.replace("ù", "u")
        fixed = fixed.replace("ç", "c")

        return fixed


class TextNormalizerRegistry:
    """Registry for text normalizer implementations.

    This registry manages different text normalizer implementations
    that may be provided by plugins.
    """

    _normalizers: Dict[str, Type[TextNormalizer]] = {}

    @classmethod
    def register(cls, name: str, normalizer_class: Type[TextNormalizer]) -> None:
        """Register a text normalizer implementation.

        Args:
            name: Unique name for the normalizer
            normalizer_class: TextNormalizer implementation class
        """
        cls._normalizers[name] = normalizer_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[TextNormalizer]]:
        """Get a text normalizer implementation by name.

        Args:
            name: Normalizer name

        Returns:
            TextNormalizer implementation class or None if not found
        """
        return cls._normalizers.get(name)

    @classmethod
    def list(cls) -> List[str]:
        """List all registered normalizer names.

        Returns:
            List of normalizer names
        """
        return list(cls._normalizers.keys())

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> TextNormalizer:
        """Create a text normalizer instance.

        Args:
            name: Normalizer name
            **kwargs: Configuration options for the normalizer

        Returns:
            TextNormalizer instance

        Raises:
            TextNormalizationError: If normalizer not found
        """
        normalizer_class = cls.get(name)
        if not normalizer_class:
            raise TextNormalizationError(f"Text normalizer not found: {name}")

        return normalizer_class(**kwargs)


# Register the base text normalizer
TextNormalizerRegistry.register("base", BaseTextNormalizer)
