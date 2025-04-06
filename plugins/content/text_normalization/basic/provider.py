"""Basic text normalization provider for PepperPy."""

import re
from re import Pattern
from typing import Any, TypeVar

from pepperpy.content.processors.text_normalization_base import BaseTextNormalizer
from pepperpy.core.base import PepperpyError
from pepperpy.core.logging import get_logger
from pepperpy.core.registry import Registry

T = TypeVar("T", bound="BasicTextNormalizer")
logger = get_logger(__name__)


class BasicTextNormalizer(BaseTextNormalizer):
    """Basic text normalization provider.

    This provider implements simple text normalization with configurable
    transformations like lowercase, whitespace stripping, and stopword removal.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the basic text normalizer.

        Args:
            **kwargs: Configuration options including:
                - language: Language code (default: en)
                - transformations: List of transformations to apply
                - remove_stopwords: Whether to remove stopwords (default: False)
                - custom_patterns: List of regex patterns to remove
                - custom_replacements: Custom character replacements
        """
        super().__init__(**kwargs)
        self._patterns: list[Pattern[str]] = []
        self._stopwords: set[str] | None = None
        self.remove_stopwords: bool = kwargs.get("remove_stopwords", False)
        self.custom_patterns: list[str] = kwargs.get("custom_patterns", [])

    async def initialize(self) -> None:
        """Initialize the provider."""
        try:
            # Initialize stopwords if needed
            if self.remove_stopwords:
                self._load_stopwords()

            # Pre-compile regex patterns
            self._patterns = []
            for pattern in self.custom_patterns:
                self._patterns.append(re.compile(pattern))

        except Exception as e:
            raise PepperpyError(f"Failed to initialize basic text normalizer: {e}")

    def _load_stopwords(self) -> None:
        """Load stopwords for the configured language."""
        try:
            import nltk  # type: ignore

            nltk.download("stopwords", quiet=True)
            from nltk.corpus import stopwords  # type: ignore

            self._stopwords = set(stopwords.words(self.language))
        except ImportError:
            logger.warning("NLTK not installed, stopword removal disabled")
            self._stopwords = set()
        except Exception as e:
            logger.warning(f"Failed to load stopwords: {e!s}")
            self._stopwords = set()

    def normalize(self, text: str) -> str:
        """Normalize the input text using configured transformations.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text
        """
        # First apply base normalizations
        text = super().normalize(text)

        # Apply basic transformations
        if "lowercase" in self.transformations:
            text = text.lower()
        if "strip_whitespace" in self.transformations:
            text = " ".join(text.split())
        if "remove_stopwords" in self.transformations and self._stopwords:
            words = text.split()
            text = " ".join(w for w in words if w not in self._stopwords)

        # Apply custom regex patterns
        for pattern in self._patterns:
            text = pattern.sub("", text)

        return text


# Register the plugin's normalizer in the registry
Registry.register_provider("text_normalizer", "basic", BasicTextNormalizer)
