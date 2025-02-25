"""Base functionality for the unified observability system.

This module provides the core abstractions and base classes for metrics,
logging, tracing, and health checks in a unified observability system.
"""

from abc import ABC, abstractmethod
from typing import Any

from .types import (
    Context,
    LogLevel,
    MetricType,
    MetricValue,
    Span,
    Tags,
)


class ObservabilityProvider(ABC):
    """Base class for observability providers.

    This class defines the interface that all observability providers must implement.
    It provides methods for metrics, logging, tracing, and health checks.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the observability provider.

        This method must be called before using the provider.
        It will initialize any required resources and start background tasks.

        Raises:
            ObservabilityError: If initialization fails
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the observability provider.

        This method must be called when the provider is no longer needed.
        It will clean up any allocated resources and stop background tasks.

        Raises:
            ObservabilityError: If cleanup fails
        """
        pass

    # Metrics
    @abstractmethod
    async def record_metric(
        self,
        name: str,
        value: MetricValue,
        type: MetricType,
        tags: Tags | None = None,
        description: str | None = None,
    ) -> None:
        """Record a metric measurement.

        Args:
            name: Name of the metric
            value: Metric value
            type: Type of metric
            tags: Optional tags for metric categorization
            description: Optional metric description

        Raises:
            ObservabilityError: If recording fails
        """
        pass

    # Logging
    @abstractmethod
    async def log(
        self,
        message: str,
        level: LogLevel,
        context: Context | None = None,
    ) -> None:
        """Log a message with structured context.

        Args:
            message: Log message
            level: Log level
            context: Optional structured context

        Raises:
            ObservabilityError: If logging fails
        """
        pass

    # Tracing
    @abstractmethod
    async def start_span(
        self,
        name: str,
        parent_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Start a new tracing span.

        Args:
            name: Name of the span
            parent_id: Optional ID of parent span
            attributes: Optional span attributes

        Returns:
            The created span

        Raises:
            ObservabilityError: If span creation fails
        """
        pass

    @abstractmethod
    async def end_span(
        self,
        span: Span,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """End a tracing span.

        Args:
            span: The span to end
            attributes: Optional attributes to add

        Raises:
            ObservabilityError: If span completion fails
        """
        pass
