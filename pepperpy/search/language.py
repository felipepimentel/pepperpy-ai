"""Language detection and tokenization for multi-language support.

This module provides functionality for detecting languages and performing
language-specific tokenization for improved full-text search capabilities.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import ParamSpec, Protocol, TypeVar

import langdetect
from langdetect.detector_factory import DetectorFactory
from nltk.stem import PorterStemmer, SnowballStemmer, WordNetLemmatizer
from pydantic import BaseModel

from pepperpy.monitoring import logger, tracer

# Set seed for consistent language detection
DetectorFactory.seed = 0

T = TypeVar("T")
P = ParamSpec("P")


def trace(name: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to trace function execution.

    Args:
        name: Name of the trace.

    Returns:
        Decorated function.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            with tracer.start_trace(name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class Language(str, Enum):
    """Supported languages for text analysis."""

    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    DUTCH = "nl"
    RUSSIAN = "ru"
    JAPANESE = "ja"
    CHINESE = "zh"
    KOREAN = "ko"
    ARABIC = "ar"
    HINDI = "hi"
    TURKISH = "tr"
    VIETNAMESE = "vi"


class Stemmer(Protocol):
    """Protocol for stemmers."""

    def stem(self, word: str) -> str:
        """Stem a word.

        Args:
            word: Word to stem

        Returns:
            Stemmed word
        """
        ...


class Lemmatizer(Protocol):
    """Protocol for lemmatizers."""

    def lemmatize(self, word: str) -> str:
        """Lemmatize a word.

        Args:
            word: Word to lemmatize

        Returns:
            Lemmatized word
        """
        ...


@dataclass
class TokenizationResult:
    """Result of text tokenization."""

    tokens: list[str]
    language: Language
    confidence: float
    metadata: dict[str, str]


class LanguageConfig(BaseModel):
    """Configuration for language detection and tokenization."""

    min_confidence: float = 0.8
    fallback_language: Language = Language.ENGLISH
    enable_stemming: bool = True
    enable_lemmatization: bool = True
    remove_stopwords: bool = True
    min_token_length: int = 2
    max_token_length: int = 50


class LanguageProcessor:
    """Processor for language detection and tokenization."""

    def __init__(self, config: LanguageConfig) -> None:
        """Initialize the language processor.

        Args:
            config: Language processing configuration
        """
        self.config = config
        self._stopwords: dict[Language, set[str]] = {}
        self._stemmers: dict[Language, Stemmer] = {}
        self._lemmatizers: dict[Language, Lemmatizer] = {}
        self._initialize_resources()

    def _initialize_resources(self) -> None:
        """Initialize language processing resources."""
        try:
            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize

            # Initialize stemmers
            self._stemmers = {
                Language.ENGLISH: PorterStemmer(),
                Language.SPANISH: SnowballStemmer("spanish"),
                Language.FRENCH: SnowballStemmer("french"),
                Language.GERMAN: SnowballStemmer("german"),
                Language.ITALIAN: SnowballStemmer("italian"),
                Language.PORTUGUESE: SnowballStemmer("portuguese"),
                Language.DUTCH: SnowballStemmer("dutch"),
                Language.RUSSIAN: SnowballStemmer("russian"),
            }

            # Initialize lemmatizers
            self._lemmatizers = {
                Language.ENGLISH: WordNetLemmatizer(),
            }

            # Load stopwords for supported languages
            for lang in Language:
                try:
                    self._stopwords[lang] = set(stopwords.words(lang.value))
                except OSError:
                    logger.warning(
                        "Stopwords not available for language",
                        language=lang.value,
                    )

            self._word_tokenize = word_tokenize
            logger.info("Initialized language processing resources")

        except ImportError as e:
            logger.error(
                "Failed to initialize language resources",
                error=str(e),
            )
            raise

    @trace("detect_language")
    def detect_language(self, text: str) -> tuple[Language, float]:
        """Detect the language of a text.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (detected language, confidence score)
        """
        try:
            detection = langdetect.detect_langs(text)[0]
            lang_code = detection.lang
            confidence = detection.prob

            # Map to supported language or fallback
            try:
                language = Language(lang_code)
            except ValueError:
                language = self.config.fallback_language
                logger.warning(
                    "Unsupported language detected, using fallback",
                    detected=lang_code,
                    fallback=language.value,
                )

            return language, confidence

        except langdetect.LangDetectException as e:
            logger.warning(
                "Language detection failed",
                error=str(e),
                fallback=self.config.fallback_language.value,
            )
            return self.config.fallback_language, 0.0

    @trace("tokenize_text")
    def tokenize_text(
        self, text: str, language: Language | None = None
    ) -> TokenizationResult:
        """Tokenize text with language-specific processing.

        Args:
            text: Text to tokenize
            language: Optional known language (will be detected if not provided)

        Returns:
            Tokenization result with tokens and metadata
        """
        # Detect language if not provided
        if language is None:
            language, confidence = self.detect_language(text)
        else:
            confidence = 1.0

        # Tokenize text
        tokens = self._word_tokenize(text)

        # Apply length filters
        tokens = [
            token
            for token in tokens
            if self.config.min_token_length
            <= len(token)
            <= self.config.max_token_length
        ]

        # Remove stopwords if enabled
        if self.config.remove_stopwords and language in self._stopwords:
            tokens = [
                token
                for token in tokens
                if token.lower() not in self._stopwords[language]
            ]

        # Apply stemming if enabled
        if self.config.enable_stemming and language in self._stemmers:
            stemmer = self._stemmers[language]
            tokens = [stemmer.stem(token) for token in tokens]

        # Apply lemmatization if enabled
        if self.config.enable_lemmatization and language in self._lemmatizers:
            lemmatizer = self._lemmatizers[language]
            tokens = [lemmatizer.lemmatize(token) for token in tokens]

        return TokenizationResult(
            tokens=tokens,
            language=language,
            confidence=confidence,
            metadata={
                "stemming": str(self.config.enable_stemming),
                "lemmatization": str(self.config.enable_lemmatization),
                "stopwords_removed": str(self.config.remove_stopwords),
            },
        )

    @trace("get_supported_languages")
    def get_supported_languages(self) -> dict[str, dict[str, bool]]:
        """Get information about supported languages and features.

        Returns:
            Dictionary mapping language codes to feature support
        """
        return {
            lang.value: {
                "stemming": lang in self._stemmers,
                "lemmatization": lang in self._lemmatizers,
                "stopwords": lang in self._stopwords,
            }
            for lang in Language
        }
