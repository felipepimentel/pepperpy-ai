"""NLTK-based text normalization provider."""

import logging
from typing import Any, TypeVar, cast

# Type ignore for NLTK imports since it lacks type stubs
import nltk  # type: ignore
from nltk.tokenize import word_tokenize  # type: ignore
from pepperpy.content.processors.text_normalization_base import BaseTextNormalizer
from pepperpy.core.base import PepperpyError
from pepperpy.core.registry import Registry

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="NLTKTextNormalizer")


class NLTKTextNormalizer(BaseTextNormalizer):
    """Text normalizer using NLTK."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the normalizer.

        Args:
            **kwargs: Configuration options including:
                - language: Language code (default: en)
                - use_lemmatization: Whether to use lemmatization (default: True)
                - remove_stopwords: Whether to remove stopwords (default: True)
                - transformations: List of transformations to apply
                - custom_patterns: Custom regex patterns
                - custom_replacements: Custom character replacements
        """
        super().__init__(**kwargs)
        self._tokenizer: Any | None = None
        self._lemmatizer: Any | None = None
        self._stopwords: set | None = None
        self.use_lemmatization: bool = kwargs.get("use_lemmatization", True)
        self.remove_stopwords: bool = kwargs.get("remove_stopwords", True)

    async def initialize(self) -> None:
        """Initialize NLTK resources."""
        try:
            # Download required NLTK data
            nltk.download("punkt", quiet=True)
            if self.use_lemmatization:
                nltk.download("wordnet", quiet=True)
            if self.remove_stopwords:
                nltk.download("stopwords", quiet=True)

            # Initialize components
            self._tokenizer = word_tokenize
            if self.use_lemmatization:
                from nltk.stem import WordNetLemmatizer  # type: ignore

                self._lemmatizer = WordNetLemmatizer()
            if self.remove_stopwords:
                from nltk.corpus import stopwords  # type: ignore

                self._stopwords = set(stopwords.words(self.language))

        except Exception as e:
            raise PepperpyError(f"Failed to initialize NLTK resources: {e}")

    def normalize(self, text: str) -> str:
        """Apply NLTK-based normalization to text.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # First apply base normalizations
        text = super().normalize(text)

        # Tokenize
        tokens = self.transform_tokenize_words(text)

        # Apply NLTK-specific transformations
        if self.use_lemmatization:
            tokens = self.transform_lemmatize(tokens)
        if self.remove_stopwords:
            tokens = self.transform_remove_stopwords(tokens)

        # Join tokens back into text
        return self.transform_join_words(tokens)

    def transform_tokenize_words(self, text: str) -> list[str]:
        """Tokenize text into words using NLTK."""
        if not self._tokenizer:
            return text.split()
        return cast(list[str], self._tokenizer(text))

    def transform_lemmatize(self, tokens: list[str]) -> list[str]:
        """Lemmatize tokens using NLTK."""
        if not self._lemmatizer or not self.use_lemmatization:
            return tokens
        return [self._lemmatizer.lemmatize(token) for token in tokens]

    def transform_remove_stopwords(self, tokens: list[str]) -> list[str]:
        """Remove stopwords using NLTK."""
        if not self._stopwords or not self.remove_stopwords:
            return tokens
        return [token for token in tokens if token.lower() not in self._stopwords]

    def transform_join_words(self, tokens: list[str]) -> str:
        """Join tokens back into text."""
        return " ".join(tokens)


# Register the plugin's normalizer in the registry
Registry.register_provider("text_normalizer", "nltk", NLTKTextNormalizer)


# Provider factory function (required by plugin system)
def create_provider(**kwargs: Any) -> NLTKTextNormalizer:
    """Create an NLTK text normalizer provider.

    Args:
        **kwargs: Configuration options

    Returns:
        NLTKTextNormalizer instance
    """
    return NLTKTextNormalizer(**kwargs)
