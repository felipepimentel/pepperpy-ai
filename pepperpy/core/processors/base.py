"""@file: base.py
@purpose: Core processor base classes and types
@component: Core > Processors
@created: 2024-03-21
@task: TASK-007-R060
@status: active
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pepperpy.core.errors import ProcessingError
from pepperpy.core.metrics import MetricsManager

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class ProcessingContext:
    """Context for content processing."""

    content_type: str
    metadata: dict[str, Any]
    options: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessingResult(Generic[R]):
    """Result of content processing."""

    content: R
    metadata: dict[str, Any]
    errors: list[str]
    warnings: list[str]
    processing_time: float


class ContentProcessor(ABC, Generic[T, R]):
    """Base class for content processors."""

    def __init__(self):
        self._metrics = MetricsManager.get_instance()

    @abstractmethod
    async def process(
        self, content: T, context: ProcessingContext
    ) -> ProcessingResult[R]:
        """Process content."""
        raise NotImplementedError

    @abstractmethod
    async def validate(self, content: T, context: ProcessingContext) -> list[str]:
        """Validate content."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        raise NotImplementedError

    async def _record_metrics(
        self, operation: str, success: bool, duration: float, **labels: str
    ) -> None:
        """Record processing metrics."""
        self._metrics.counter(
            f"processor_{operation}",
            1,
            processor=self.__class__.__name__,
            success=str(success).lower(),
            **labels,
        )
        self._metrics.histogram(
            f"processor_{operation}_duration",
            duration,
            processor=self.__class__.__name__,
            **labels,
        )


class ProcessorRegistry:
    """Registry for content processors."""

    _instance: Optional["ProcessorRegistry"] = None

    def __init__(self):
        if ProcessorRegistry._instance is not None:
            raise RuntimeError("Use get_instance() instead")
        self._processors: dict[str, dict[str, ContentProcessor]] = {}
        self._metrics = MetricsManager.get_instance()
        ProcessorRegistry._instance = self

    @classmethod
    def get_instance(cls) -> "ProcessorRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(
        self, content_type: str, version: str, processor: ContentProcessor
    ) -> None:
        """Register a content processor."""
        if content_type not in self._processors:
            self._processors[content_type] = {}
        self._processors[content_type][version] = processor
        self._metrics.counter(
            "processor_registered", 1, content_type=content_type, version=version
        )

    async def get_processor(
        self, content_type: str, version: str | None = None
    ) -> ContentProcessor:
        """Get content processor."""
        if content_type not in self._processors:
            raise ProcessingError(f"Processor not found: {content_type}")

        processors = self._processors[content_type]
        if not version:
            # Get latest version
            version = max(processors.keys())

        if version not in processors:
            raise ProcessingError(f"Version not found: {version}")

        return processors[version]

    def list_processors(self) -> dict[str, list[str]]:
        """List all registered processors."""
        return {
            content_type: list(versions.keys())
            for content_type, versions in self._processors.items()
        }
