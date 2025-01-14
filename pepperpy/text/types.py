"""Text processing types."""

from dataclasses import dataclass, field
from typing import Any

from ..types import JsonDict


@dataclass
class TextMetadata:
    """Text metadata."""

    language: str
    word_count: int
    sentence_count: int
    avg_word_length: float
    avg_sentence_length: float
    complexity_score: float
    settings: JsonDict = field(default_factory=dict)


@dataclass
class TextAnalysisResult:
    """Text analysis result."""

    text: str
    metadata: TextMetadata
    annotations: dict[str, Any] = field(default_factory=dict)
    stats: JsonDict = field(default_factory=dict)


@dataclass
class ChunkMetadata:
    """Text chunk metadata."""

    index: int
    start: int
    end: int
    overlap: int | None = None
    settings: JsonDict = field(default_factory=dict)


@dataclass
class ChunkResult:
    """Text chunk result."""

    text: str
    metadata: ChunkMetadata
    annotations: dict[str, Any] = field(default_factory=dict)
