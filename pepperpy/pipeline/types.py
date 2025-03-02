"""Type definitions for the pipeline system."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class PipelineType(Enum):
    """Types of pipeline processing."""

    BATCH = auto()
    STREAM = auto()
    HYBRID = auto()


class ProcessingMode(Enum):
    """Processing modes for pipeline execution."""

    SEQUENTIAL = auto()
    PARALLEL = auto()
    DISTRIBUTED = auto()


class ProcessingStatus(Enum):
    """Status of processing operations."""

    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class PipelineConfig:
    """Configuration for pipeline providers."""

    name: str
    pipeline_type: PipelineType
    processing_mode: ProcessingMode = ProcessingMode.SEQUENTIAL
    batch_size: Optional[int] = None
    timeout: Optional[float] = None
    retry_count: int = 0
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineStats:
    """Statistics for pipeline execution."""

    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
