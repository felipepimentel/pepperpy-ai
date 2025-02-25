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
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pepperpy.core.metrics import Counter, Histogram
from pepperpy.core.errors import ProcessingError

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class ProcessingContext:
    """Context for content processing.
    
    Args:
        content_type: Type of content being processed
        metadata: Additional metadata for processing
        options: Processing options
        timestamp: Processing timestamp
    """

    content_type: str
    metadata: Dict[str, Any]
    options: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessingResult(Generic[R]):
    """Result of content processing.
    
    Args:
        content: Processed content
        metadata: Processing metadata
        errors: List of errors encountered
        warnings: List of warnings generated
        processing_time: Time taken to process
    """

    content: R
    metadata: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    processing_time: float


class ContentProcessor(ABC, Generic[T, R]):
    """Base class for content processors."""

    def __init__(self):
        """Initialize processor with metrics."""
        self._process_counter = Counter(
            "processor_process_total",
            "Total number of content processing operations",
            ["processor", "content_type", "success"]
        )
        self._process_duration = Histogram(
            "processor_process_duration_seconds",
            "Duration of content processing operations",
            ["processor", "content_type"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        )

    @abstractmethod
    async def process(
        self, content: T, context: ProcessingContext
    ) -> ProcessingResult[R]:
        """Process content.
        
        Args:
            content: Content to process
            context: Processing context
            
        Returns:
            ProcessingResult containing processed content
        """
        raise NotImplementedError

    @abstractmethod
    async def validate(
        self, content: T, context: ProcessingContext
    ) -> List[str]:
        """Validate content.
        
        Args:
            content: Content to validate
            context: Validation context
            
        Returns:
            List of validation errors
        """
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        raise NotImplementedError

    async def _record_metrics(
        self, operation: str, success: bool, duration: float, **labels: str
    ) -> None:
        """Record processing metrics.
        
        Args:
            operation: Operation being measured
            success: Whether operation succeeded
            duration: Operation duration
            **labels: Additional metric labels
        """
        self._process_counter.inc(
            1.0,
            labels={
                "processor": self.__class__.__name__,
                "content_type": labels.get("content_type", "unknown"),
                "success": str(success).lower()
            }
        )
        self._process_duration.observe(
            duration,
            labels={
                "processor": self.__class__.__name__,
                "content_type": labels.get("content_type", "unknown")
            }
        )


class ProcessorRegistry:
    """Registry for content processors."""

    _instance: Optional["ProcessorRegistry"] = None

    def __init__(self):
        """Initialize registry."""
        if ProcessorRegistry._instance is not None:
            raise RuntimeError("Use get_instance() instead")
        self._processors: Dict[str, Dict[str, ContentProcessor]] = {}
        self._register_counter = Counter(
            "processor_registered_total",
            "Total number of registered processors",
            ["content_type", "version"]
        )
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
        """Register a content processor.
        
        Args:
            content_type: Type of content the processor handles
            version: Processor version
            processor: Processor instance
        """
        if content_type not in self._processors:
            self._processors[content_type] = {}
        self._processors[content_type][version] = processor
        self._register_counter.inc(
            1.0,
            labels={
                "content_type": content_type,
                "version": version
            }
        )

    async def get_processor(
        self, content_type: str, version: Optional[str] = None
    ) -> ContentProcessor:
        """Get content processor.
        
        Args:
            content_type: Type of content to process
            version: Optional processor version
            
        Returns:
            Content processor instance
            
        Raises:
            ProcessingError: If processor not found
        """
        if content_type not in self._processors:
            raise ProcessingError(f"Processor not found: {content_type}")

        processors = self._processors[content_type]
        if not version:
            # Get latest version
            version = max(processors.keys())

        if version not in processors:
            raise ProcessingError(f"Version not found: {version}")

        return processors[version]

    def list_processors(self) -> Dict[str, List[str]]:
        """List all registered processors.
        
        Returns:
            Dictionary mapping content types to version lists
        """
        return {
            content_type: list(versions.keys())
            for content_type, versions in self._processors.items()
        }
