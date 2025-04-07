"""NLTK text normalizer provider.

This module provides a text normalizer implementation that uses NLTK
for advanced text processing features like lemmatization and stopword removal.
"""

import logging
from typing import Any

from pepperpy.content.base import TextNormalizationError, TextNormalizer
from pepperpy.plugin.base import PepperpyPlugin

logger = logging.getLogger(__name__)

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class NLTKTextNormalizer(TextNormalizer, PepperpyPlugin):
    """NLTK-based text normalizer implementation.

    This normalizer extends the basic normalizer with NLTK-based features
    like lemmatization and stopword removal.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the normalizer.

        Args:
            **kwargs: Configuration options
        """
        super().__init__(**kwargs)

        if not NLTK_AVAILABLE:
            raise TextNormalizationError(
                "NLTK is required but not installed. Please install nltk package."
            )

        # Get configuration
        self.transformations = kwargs.get(
            "transformations",
            [
                "strip_whitespace",
                "normalize_unicode",
                "normalize_whitespace",
                "remove_control_chars",
                "lemmatize",
                "remove_stopwords",
            ],
        )

        self.language = kwargs.get("language", "en")
        self.use_lemmatization = kwargs.get("use_lemmatization", True)
        self.use_stopwords = kwargs.get("use_stopwords", True)

        # Initialize NLTK components
        self.lemmatizer: WordNetLemmatizer | None = None
        self.stopwords: set[str] | None = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the normalizer.

        Downloads required NLTK data and initializes components.
        """
        if self.initialized:
            return

        try:
            # Download required NLTK data
            if self.use_lemmatization:
                try:
                    nltk.data.find("corpora/wordnet")
                except LookupError:
                    logger.info("Downloading WordNet...")
                    nltk.download("wordnet", quiet=True)

                self.lemmatizer = WordNetLemmatizer()

            if self.use_stopwords:
                try:
                    nltk.data.find("corpora/stopwords")
                except LookupError:
                    logger.info("Downloading stopwords...")
                    nltk.download("stopwords", quiet=True)

                try:
                    self.stopwords = set(stopwords.words(self.language))
                except OSError:
                    logger.warning(
                        f"No stopwords available for {self.language}. Using English."
                    )
                    self.stopwords = set(stopwords.words("english"))

            try:
                nltk.data.find("tokenizers/punkt")
            except LookupError:
                logger.info("Downloading Punkt tokenizer...")
                nltk.download("punkt", quiet=True)

            self.initialized = True

        except Exception as e:
            raise TextNormalizationError(f"Failed to initialize NLTK components: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        # No resources to clean up
        pass

    def normalize(self, text: str) -> str:
        """Apply all configured normalizations to text.

        Args:
            text: Input text

        Returns:
            Normalized text

        Raises:
            TextNormalizationError: If normalization fails
        """
        if not text:
            return ""

        if not self.initialized:
            raise TextNormalizationError("Normalizer not initialized")

        result = text

        # Apply transformations in order
        for transformation in self.transformations:
            transform_method = getattr(self, f"transform_{transformation}", None)
            if transform_method and callable(transform_method):
                try:
                    result = transform_method(result)
                except Exception as e:
                    raise TextNormalizationError(f"Error in {transformation}: {e}")
            else:
                logger.warning(f"Unknown transformation: {transformation}")

        return result

    def transform_lemmatize(self, text: str) -> str:
        """Lemmatize text using NLTK WordNet lemmatizer.

        Args:
            text: Input text

        Returns:
            Lemmatized text
        """
        if not self.use_lemmatization or not self.lemmatizer:
            return text

        try:
            # Tokenize
            tokens = word_tokenize(text)

            # Lemmatize each token
            lemmatized = [self.lemmatizer.lemmatize(word) for word in tokens]

            # Join back into text
            return " ".join(lemmatized)

        except Exception as e:
            logger.warning(f"Error lemmatizing text: {e}")
            return text

    def transform_remove_stopwords(self, text: str) -> str:
        """Remove stopwords using NLTK stopwords list.

        Args:
            text: Input text

        Returns:
            Text with stopwords removed
        """
        if not self.use_stopwords or not self.stopwords:
            return text

        try:
            # Tokenize
            tokens = word_tokenize(text)

            # Filter out stopwords
            filtered = [word for word in tokens if word.lower() not in self.stopwords]

            # Join back into text
            return " ".join(filtered)

        except Exception as e:
            logger.warning(f"Error removing stopwords: {e}")
            return text
