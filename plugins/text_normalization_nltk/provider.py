"""NLTK-based text normalization provider for PepperPy."""

from typing import Any, Dict, List, Optional

from pepperpy.content_processing.processors.text_normalization_base import (
    BaseTextNormalizer,
    TextNormalizerRegistry,
)

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
except ImportError:
    nltk = None


class NLTKTextNormalizer(BaseTextNormalizer):
    """NLTK-based text normalization provider.

    This provider extends the BaseTextNormalizer with advanced linguistic
    features using NLTK, including tokenization, lemmatization, and
    stopword removal.
    """

    

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
    client: Optional[Any]
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
        """Initialize the NLTK text normalizer.

        Args:
            **kwargs: Configuration options
        """
        # Get configuration
        transformations = kwargs.get("transformations")
        custom_patterns = kwargs.get("custom_patterns")
        custom_replacements = kwargs.get("custom_replacements")
        language = kwargs.get("language", "en")
        self.use_lemmatization = kwargs.get("use_lemmatization", True)
        self.remove_stopwords = kwargs.get("remove_stopwords", True)

        # Initialize base normalizer
        super().__init__(
            transformations=transformations,
            custom_patterns=custom_patterns,
            custom_replacements=custom_replacements,
            language=language,
            **kwargs,
        )

        # Initialize NLTK resources
        self.initialized = False
        self._tokenizer = None
        self._lemmatizer = None
        self._stopwords = None

    async def initialize(self) -> None:
        """Initialize NLTK resources.

        This method downloads required NLTK data and initializes
        tokenizer, lemmatizer, and stopwords for the specified language.
        """
        if self.initialized:
            return

        try:
            if not nltk:
                raise ImportError("NLTK is not installed. Please install it with: pip install nltk")

            # Download required NLTK data
            nltk.download("punkt", quiet=True)
            nltk.download("wordnet", quiet=True)
            nltk.download("stopwords", quiet=True)
            nltk.download("averaged_perceptron_tagger", quiet=True)

            # Initialize components
            self._tokenizer = word_tokenize
            self._lemmatizer = WordNetLemmatizer()

            # Map language code to NLTK language name
            nltk_language = self.LANGUAGE_MAP.get(self.language, "english")
            self._stopwords = set(stopwords.words(nltk_language))

            self.initialized = True

        except ImportError as e:
            raise ImportError(
                "NLTK is required for this provider. " "Install with: pip install nltk"
            ) from e

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        self._tokenizer = None
        self._lemmatizer = None
        self._stopwords = None
        self.initialized = False

    def transform_tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words using NLTK.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        if not self._tokenizer:
            return text.split()
        return self._tokenizer(text)

    def transform_lemmatize(self, tokens: List[str]) -> List[str]:
        """Lemmatize tokens using NLTK.

        Args:
            tokens: List of tokens

        Returns:
            List of lemmatized tokens
        """
        if not self._lemmatizer or not self.use_lemmatization:
            return tokens
        return [self._lemmatizer.lemmatize(token) for token in tokens]

    def transform_remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove stopwords using NLTK.

        Args:
            tokens: List of tokens

        Returns:
            List of tokens with stopwords removed
        """
        if not self._stopwords or not self.remove_stopwords:
            return tokens
        return [token for token in tokens if token.lower() not in self._stopwords]

    def transform_join_words(self, tokens: List[str]) -> str:
        """Join tokens back into text.

        Args:
            tokens: List of tokens

        Returns:
            Joined text
        """
        return " ".join(tokens)

    def normalize(self, text: str) -> str:
        """Apply all configured normalizations to text.

        This implementation extends the base normalizer with NLTK-specific
        transformations for linguistic processing.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
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
