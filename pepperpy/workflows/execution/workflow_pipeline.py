"""Workflow processing pipeline implementation.

This module provides the core workflow processing pipeline functionality:
- Pipeline configuration and execution
- Processor chaining
- Metrics collection
- Validation
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import ValidationError
from pepperpy.core.models import BaseModel, Field
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.monitoring.metrics import Counter, Histogram, MetricsManager
from pepperpy.processing.processors import BaseProcessor
from pepperpy.processing.transformers import BaseTransformer
from pepperpy.processing.validators import BaseValidator

# Type variables
T = TypeVar("T")
ProcessorType = TypeVar("ProcessorType", bound="BaseProcessor")


class WorkflowProcessingError(Exception):
    """Base class for workflow processing errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message)
        self.details = details or {}


class WorkflowProcessingResult(BaseModel):
    """Result of workflow processing operation.

    Attributes:
        success: Whether processing was successful
        data: Processed data
        error: Optional error information
        metrics: Processing metrics
    """

    success: bool = Field(description="Whether processing was successful")
    data: Any = Field(description="Processed data")
    error: dict[str, Any] | None = Field(default=None, description="Error information")
    metrics: dict[str, Any] = Field(
        default_factory=dict, description="Processing metrics"
    )


class WorkflowPipeline(Lifecycle, Generic[T]):
    """Workflow processing pipeline implementation."""

    def __init__(self) -> None:
        """Initialize pipeline."""
        super().__init__()
        self._processors: list[BaseProcessor] = []
        self._transformers: list[BaseTransformer] = []
        self._validators: list[BaseValidator] = []
        self._metrics = MetricsManager()
        self._state = ComponentState.CREATED

        # Initialize metrics
        self._total_counter: Counter | None = None
        self._error_counter: Counter | None = None
        self._latency_histogram: Histogram | None = None

    async def initialize(self) -> None:
        """Initialize pipeline."""
        try:
            # Set up metrics
            self._total_counter = await self._metrics.create_counter(
                "workflow_processing_total",
                "Total number of workflow processing operations",
            )
            self._error_counter = await self._metrics.create_counter(
                "workflow_processing_errors",
                "Number of workflow processing errors",
            )
            self._latency_histogram = await self._metrics.create_histogram(
                "workflow_processing_latency",
                "Workflow processing operation latency",
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            )

            self._state = ComponentState.READY
            logger.info("Workflow processing pipeline initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize workflow processing pipeline: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up pipeline resources."""
        try:
            self._processors.clear()
            self._transformers.clear()
            self._validators.clear()
            self._state = ComponentState.CLEANED
            logger.info("Workflow processing pipeline cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup workflow processing pipeline: {e}")
            raise

    async def _record_success(self) -> None:
        """Record successful processing."""
        if self._total_counter:
            await self._total_counter.inc()

    async def _record_error(self) -> None:
        """Record processing error."""
        if self._error_counter:
            await self._error_counter.inc()

    async def _record_latency(self, duration: float) -> None:
        """Record processing latency.

        Args:
            duration: Processing duration in seconds
        """
        if self._latency_histogram:
            await self._latency_histogram.observe(duration)

    def add_processor(self, processor: BaseProcessor) -> None:
        """Add processor to pipeline.

        Args:
            processor: Processor to add
        """
        self._processors.append(processor)

    def add_transformer(self, transformer: BaseTransformer) -> None:
        """Add transformer to pipeline.

        Args:
            transformer: Transformer to add
        """
        self._transformers.append(transformer)

    def add_validator(self, validator: BaseValidator) -> None:
        """Add validator to pipeline.

        Args:
            validator: Validator to add
        """
        self._validators.append(validator)

    async def process(self, data: T, **kwargs: Any) -> WorkflowProcessingResult:
        """Process data through pipeline.

        Args:
            data: Data to process
            **kwargs: Additional processing parameters

        Returns:
            Processing result

        Raises:
            WorkflowProcessingError: If processing fails
        """
        if self._state != ComponentState.READY:
            raise WorkflowProcessingError("Pipeline not running")

        start_time = datetime.utcnow()

        try:
            # Apply transformers
            transformed_data = data
            for transformer in self._transformers:
                transformed_data = await transformer.transform(transformed_data)

            # Run validators
            for validator in self._validators:
                try:
                    await validator.validate(transformed_data)
                except ValidationError as e:
                    await self._record_error()
                    return WorkflowProcessingResult(
                        success=False,
                        data=transformed_data,
                        error={"type": "validation", "details": e.details},
                        metrics={"duration": 0.0},
                    )

            # Execute processors
            processed_data = transformed_data
            for processor in self._processors:
                processed_data = await processor.process(processed_data, **kwargs)

            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._record_success()
            await self._record_latency(duration)

            return WorkflowProcessingResult(
                success=True,
                data=processed_data,
                metrics={"duration": duration},
            )

        except Exception as e:
            # Record error
            await self._record_error()

            # Log error
            logger.error(
                "Workflow processing error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            # Return error result
            return WorkflowProcessingResult(
                success=False,
                data=data,
                error={
                    "type": type(e).__name__,
                    "message": str(e),
                    "details": getattr(e, "details", None),
                },
                metrics={"duration": 0.0},
            )
