"""Text processing configuration."""

from dataclasses import dataclass, field

from ..types import JsonDict


@dataclass
class ProcessorConfig:
    """Base text processor configuration."""

    name: str
    enabled: bool = True
    settings: JsonDict = field(default_factory=dict)
    metadata: JsonDict = field(default_factory=dict)


@dataclass
class ChunkerConfig(ProcessorConfig):
    """Text chunker configuration."""

    chunk_size: int = 1000
    overlap: int = 200
    min_chunk_size: int | None = None
    max_chunk_size: int | None = None


@dataclass
class AnalyzerConfig(ProcessorConfig):
    """Text analyzer configuration."""

    min_length: int = 10
    max_length: int = 100000
    language: str | None = None
    complexity_threshold: float = 0.5
