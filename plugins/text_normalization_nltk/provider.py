"""NLTK-based text normalization provider for PepperPy."""

import os
from typing import Any, List, Optional, Type, TypeVar, cast

from pepperpy.content_processing.processors.text_normalization_base import (
    BaseTextNormalizer,
    TextNormalizerRegistry,
)
from pepperpy.core import ConfigError, ProviderError
from pepperpy.plugin import ProviderPlugin

T = TypeVar("T", bound="NLTKTextNormalizer")


class NLTKTextNormalizer(BaseTextNormalizer, ProviderPlugin):
    """NLTK-based text normalization provider."""

    # Fixed values with defaults
    nltk_data_dir: str = os.path.expanduser("~/.nltk_data")
    use_lemmatization: bool = True
    remove_stopwords: bool = True
    language: str = "en"

    # Runtime state (not from config)
    _tokenizer: Optional[Any] = None
    _lemmatizer: Optional[Any] = None
    _stopwords: Optional[set] = None

    LANGUAGE_MAP = {
        "en": "english",
        "pt": "portuguese",
        "es": "spanish",
        "fr": "french",
        "de": "german",
        "it": "italian",
        "nl": "dutch",
        "ru": "russian",
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the NLTK text normalizer."""
        super().__init__(**kwargs)

        # Override fixed values if provided
        if "use_lemmatization" in kwargs:
            self.use_lemmatization = kwargs["use_lemmatization"]
        if "remove_stopwords" in kwargs:
            self.remove_stopwords = kwargs["remove_stopwords"]
        if "language" in kwargs:
            self.language = kwargs["language"]

    @classmethod
    def from_config(cls: Type[T], **config: Any) -> T:
        """Create provider instance from configuration."""
        return cast(T, cls(**config))

    async def initialize(self) -> None:
        """Initialize NLTK resources."""
        try:
            # Lazy import NLTK
            try:
                import nltk
                from nltk.corpus import stopwords
                from nltk.stem import WordNetLemmatizer
                from nltk.tokenize import word_tokenize
            except ImportError:
                raise ConfigError(
                    "NLTK is not installed. Please install it with: pip install nltk"
                )

            # Create NLTK data directory
            os.makedirs(self.nltk_data_dir, exist_ok=True)

            # Download required NLTK data
            resources = ["punkt", "wordnet", "stopwords", "averaged_perceptron_tagger"]
            for resource in resources:
                try:
                    nltk.data.find(f"tokenizers/{resource}")
                except LookupError:
                    nltk.download(resource, download_dir=self.nltk_data_dir, quiet=True)

            # Initialize components
            self._tokenizer = word_tokenize
            self._lemmatizer = WordNetLemmatizer()

            # Map language code to NLTK language name
            nltk_language = self.LANGUAGE_MAP.get(self.language, "english")
            self._stopwords = set(stopwords.words(nltk_language))

        except Exception as e:
            raise ProviderError(f"Failed to initialize NLTK resources: {e}") from e

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        self._tokenizer = None
        self._lemmatizer = None
        self._stopwords = None

    def transform_tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words using NLTK."""
        if not self._tokenizer:
            return text.split()
        return self._tokenizer(text)

    def transform_lemmatize(self, tokens: List[str]) -> List[str]:
        """Lemmatize tokens using NLTK."""
        if not self._lemmatizer or not self.use_lemmatization:
            return tokens
        return [self._lemmatizer.lemmatize(token) for token in tokens]

    def transform_remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove stopwords using NLTK."""
        if not self._stopwords or not self.remove_stopwords:
            return tokens
        return [token for token in tokens if token.lower() not in self._stopwords]

    def transform_join_words(self, tokens: List[str]) -> str:
        """Join tokens back into text."""
        return " ".join(tokens)

    def normalize(self, text: str) -> str:
        """Apply all configured normalizations to text."""
        if not text:
            return ""

        # Apply base transformations first
        result = super().normalize(text)

        # Apply NLTK transformations
        tokens = self.transform_tokenize_words(result)
        tokens = self.transform_lemmatize(tokens)
        tokens = self.transform_remove_stopwords(tokens)
        result = self.transform_join_words(tokens)

        return result


# Register the plugin's normalizer in the registry
TextNormalizerRegistry.register("nltk", NLTKTextNormalizer)


# Provider factory function (required by plugin system)
def create_provider(**kwargs: Any) -> NLTKTextNormalizer:
    """Create an NLTK text normalizer provider.

    Args:
        **kwargs: Configuration options

    Returns:
        NLTKTextNormalizer instance
    """
    return NLTKTextNormalizer(**kwargs)
