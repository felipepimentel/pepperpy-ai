"""Basic text normalization provider for PepperPy."""

import re
from re import Pattern
from typing import Any, List, Optional, Set, Type, TypeVar, cast

from pepperpy.content.processors.text_normalization_base import (
    TextNormalizer,
    TextNormalizerRegistry,
)
from pepperpy.core.logging import get_logger
from pepperpy.plugin.plugin import PepperpyPlugin

T = TypeVar("T", bound="BasicTextNormalizer")


class BasicTextNormalizer(TextNormalizer, PepperpyPlugin):
    """Basic text normalization provider.

    This provider implements the TextNormalizer interface and extends
    the BaseTextNormalizer with plugin management capabilities.
    """

    name = "basic_text_normalizer"
    version = "0.1.0"
    description = "Basic text normalization provider with configurable transformations"
    author = "PepperPy Team"

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
    client: Optional[Any]
    language: str = "en"
    transformations: List[str] = ["lowercase", "strip_whitespace"]
    remove_stopwords: bool = False
    custom_patterns: List[str] = []
    _patterns: List[Pattern[str]] = []
    _stopwords: Optional[Set[str]] = None
    logger = get_logger(__name__)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the basic text normalizer.

        Args:
            **kwargs: Configuration options
        """
        # Get configuration
        transformations = kwargs.get("transformations")
        custom_patterns = kwargs.get("custom_patterns")
        custom_replacements = kwargs.get("custom_replacements")
        language = kwargs.get("language", "en")

        # Initialize base normalizer
        super().__init__(
            transformations=transformations,
            custom_patterns=custom_patterns,
            custom_replacements=custom_replacements,
            language=language,
            **kwargs,
        )

        # Initialize provider state
        self.initialized = False

    @classmethod
    def from_config(cls: Type[T], **config: Any) -> T:
        """Create provider instance from configuration."""
        return cast(T, cls(**config))

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is required by the BaseProvider interface.
        """
        if self.initialized:
            return

        # Initialize resources
        if self.remove_stopwords:
            self._load_stopwords()

        # Pre-compile regex patterns
        self._patterns = []
        for pattern in self.custom_patterns:
            self._patterns.append(re.compile(pattern))

        self.initialized = True
        self.logger.debug(
            f"Initialized with language={self.language}, transformations={self.transformations}"
        )

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is required by the BaseProvider interface.
        """
        # Release resources
        self._patterns = []
        self._stopwords = None

        self.initialized = False
        self.logger.debug("Resources cleaned up")

    def _load_stopwords(self) -> None:
        """Load stopwords for the configured language."""
        try:
            import nltk

            nltk.download("stopwords", quiet=True)
            from nltk.corpus import stopwords

            self._stopwords = set(stopwords.words(self.language))
        except ImportError:
            self.logger.warning("NLTK not installed, stopword removal disabled")
            self._stopwords = set()
        except Exception as e:
            self.logger.warning(f"Failed to load stopwords: {e!s}")
            self._stopwords = set()

    def normalize(self, text: str) -> str:
        """Normalize the input text using configured transformations.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text
        """
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        # Apply transformations in order
        for transform in self.transformations:
            if transform == "lowercase":
                text = text.lower()
            elif transform == "strip_whitespace":
                text = " ".join(text.split())
            elif transform == "remove_stopwords" and self._stopwords:
                words = text.split()
                text = " ".join(w for w in words if w not in self._stopwords)

        # Apply custom regex patterns
        for pattern in self._patterns:
            text = pattern.sub("", text)

        return text


# Register the plugin's normalizer in the registry
TextNormalizerRegistry.register("basic", BasicTextNormalizer)


# Provider factory function (required by plugin system)
def create_provider(**kwargs: Any) -> BasicTextNormalizer:
    """Create a basic text normalizer provider.

    Args:
        **kwargs: Configuration options

    Returns:
        BasicTextNormalizer instance
    """
    return BasicTextNormalizer(**kwargs)
