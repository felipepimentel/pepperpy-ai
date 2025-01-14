"""Text analyzer module."""

from abc import ABC, abstractmethod
from typing import TypedDict


class AnalyzerParams(TypedDict, total=False):
    """Text analyzer parameters."""

    min_length: int | None
    max_length: int | None
    min_words: int | None
    max_words: int | None
    min_sentences: int | None
    max_sentences: int | None
    min_paragraphs: int | None
    max_paragraphs: int | None


class AnalyzerResult(TypedDict, total=False):
    """Text analyzer result."""

    length: int
    words: int
    sentences: int
    paragraphs: int
    language: str | None
    sentiment: float | None
    complexity: float | None


class BaseTextAnalyzer(ABC):
    """Base text analyzer implementation."""

    @abstractmethod
    async def analyze(self, text: str, **kwargs: AnalyzerParams) -> AnalyzerResult:
        """Analyze text.

        Args:
            text: Text to analyze.
            **kwargs: Analysis parameters.

        Returns:
            AnalyzerResult: Analysis results.
        """
        pass
