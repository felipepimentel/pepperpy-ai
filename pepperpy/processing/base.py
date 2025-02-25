"""Base classes for the processing system.

This module provides the core abstractions for the processing system:
- ProcessingContext: Context for processing operations
- ProcessingResult: Result of processing operations
- ProcessorError: Base error class for processing errors
- BaseProcessor: Abstract base class for all processors
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

from pepperpy.core.logging import get_logger
from pepperpy.core.metrics import MetricsManager

T = TypeVar("T")  # Input type
R = TypeVar("R")  # Result type


@dataclass
class ProcessingContext:
    """Context for content processing.

    Args:
        content_type: Type of content being processed
        metadata: Additional metadata for processing
        options: Processing options
        timestamp: When processing started
    """

    content_type: str
    metadata: dict[str, Any]
    options: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessingResult(Generic[R]):
    """Result of content processing.

    Args:
        content: Processed content
        metadata: Additional metadata about processing
        duration: Time taken to process in seconds
        errors: Any errors that occurred during processing
    """

    content: R
    metadata: dict[str, Any]
    duration: float
    errors: list[dict[str, Any]] | None = None


class ProcessorError(Exception):
    """Base error for processor-related issues.

    Args:
        message: Error message
        processor_type: Type of processor that raised the error
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        processor_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.processor_type = processor_type
        self.details = details or {}
        super().__init__(message)


class BaseProcessor(ABC, Generic[T, R]):
    """Base class for all processors.

    This class defines the interface that all processors must implement.
    It provides basic functionality for processing content with metrics
    and logging support.

    Args:
        config: Processor configuration
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize processor with configuration.

        Args:
            config: Processor configuration
        """
        self.config = config
        self._metrics = MetricsManager.get_instance()
        self._logger = get_logger(__name__)

    @abstractmethod
    async def process(
        self, content: T, context: ProcessingContext
    ) -> ProcessingResult[R]:
        """Process content with given context.

        Args:
            content: Content to process
            context: Processing context

        Returns:
            ProcessingResult with processed content

        Raises:
            ProcessorError: If processing fails
        """
        pass

    @abstractmethod
    async def validate(self, content: T, context: ProcessingContext) -> bool:
        """Validate content before processing.

        Args:
            content: Content to validate
            context: Processing context

        Returns:
            True if content is valid

        Raises:
            ProcessorError: If validation fails
        """
        pass

    async def _track_metrics(
        self,
        duration: float,
        content_type: str,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Track processing metrics.

        Args:
            duration: Processing duration in seconds
            content_type: Type of content processed
            success: Whether processing was successful
            error: Error message if processing failed
        """
        self._metrics.processing_duration.observe(
            duration, {"processor_type": self.__class__.__name__}
        )

        if not success and error:
            self._metrics.processing_errors.inc({
                "processor_type": self.__class__.__name__,
                "error_type": error,
            })

    async def _log_processing(
        self,
        context: ProcessingContext,
        success: bool,
        duration: float,
        error: str | None = None,
    ) -> None:
        """Log processing details.

        Args:
            context: Processing context
            success: Whether processing was successful
            duration: Processing duration in seconds
            error: Error message if processing failed
        """
        log_data = {
            "processor_type": self.__class__.__name__,
            "content_type": context.content_type,
            "duration": duration,
            "success": success,
        }

        if error:
            log_data["error"] = error
            self._logger.error("Processing failed", extra=log_data)
        else:
            self._logger.info("Processing completed", extra=log_data)
