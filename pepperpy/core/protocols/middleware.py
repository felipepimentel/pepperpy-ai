"""Protocol middleware for the Pepperpy framework.

This module provides middleware components for protocol processing,
including validation, transformation, logging, and metrics collection.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar

from pepperpy.monitoring import logger
from pepperpy.monitoring.metrics import MetricsManager
from pepperpy.protocols import Event, Message

# Type variables
T = TypeVar("T")


class ProtocolMiddleware(ABC):
    """Base class for protocol middleware.

    This class defines the interface for protocol middleware components
    that can process and transform protocol data.
    """

    def __init__(self) -> None:
        """Initialize middleware."""
        self._metrics = MetricsManager.get_instance()
        self._logger = logger.getChild(self.__class__.__name__)

    @abstractmethod
    async def process(
        self,
        data: Any,
        next_middleware: Callable[[Any], Any],
    ) -> Any:
        """Process protocol data.

        Args:
            data: Data to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processed data

        Raises:
            ValueError: If data processing fails

        """


class ValidationMiddleware(ProtocolMiddleware):
    """Middleware for data validation.

    This middleware validates protocol data against defined schemas
    and constraints.
    """

    def __init__(self, schema: Optional[Dict[str, Any]] = None) -> None:
        """Initialize validation middleware.

        Args:
            schema: Optional validation schema

        """
        super().__init__()
        self._schema = schema

    async def process(
        self,
        data: Any,
        next_middleware: Callable[[Any], Any],
    ) -> Any:
        """Validate and process data.

        Args:
            data: Data to validate
            next_middleware: Next middleware in chain

        Returns:
            Any: Validated data

        Raises:
            ValueError: If validation fails

        """
        try:
            # Basic validation
            if isinstance(data, (Message, Event)):
                if not data.id:
                    raise ValueError("Missing ID")
                if not data.type:
                    raise ValueError("Missing type")

            # Schema validation if provided
            if self._schema:
                # TODO: Implement schema validation
                pass

            return await next_middleware(data)
        except Exception as e:
            self._logger.error(f"Validation failed: {e}")
            raise ValueError(f"Validation failed: {e}") from e


class LoggingMiddleware(ProtocolMiddleware):
    """Middleware for protocol logging.

    This middleware logs protocol operations and data for debugging
    and monitoring.
    """

    async def process(
        self,
        data: Any,
        next_middleware: Callable[[Any], Any],
    ) -> Any:
        """Log and process data.

        Args:
            data: Data to log
            next_middleware: Next middleware in chain

        Returns:
            Any: Processed data

        """
        start_time = datetime.utcnow()
        try:
            self._logger.debug(f"Processing data: {data}")
            result = await next_middleware(data)
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._logger.debug(f"Processed data in {duration:.3f}s: {result}")
            return result
        except Exception as e:
            self._logger.error(f"Processing failed: {e}")
            raise


class MetricsMiddleware(ProtocolMiddleware):
    """Middleware for metrics collection.

    This middleware collects metrics about protocol operations
    and performance.
    """

    async def process(
        self,
        data: Any,
        next_middleware: Callable[[Any], Any],
    ) -> Any:
        """Collect metrics and process data.

        Args:
            data: Data to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processed data

        """
        start_time = datetime.utcnow()
        try:
            # Get or create metrics
            operation_counter = await self._metrics.create_counter(
                name="protocol_operations_total",
                description="Total protocol operations",
                labels={"type": type(data).__name__},
            )
            error_counter = await self._metrics.create_counter(
                name="protocol_errors_total",
                description="Total protocol errors",
                labels={"type": type(data).__name__},
            )
            latency_histogram = await self._metrics.create_histogram(
                name="protocol_operation_latency_seconds",
                description="Protocol operation latency",
                labels={"type": type(data).__name__},
            )

            # Process data
            result = await next_middleware(data)

            # Record metrics
            await operation_counter.inc()
            duration = (datetime.utcnow() - start_time).total_seconds()
            await latency_histogram.observe(duration)

            return result
        except Exception:
            await error_counter.inc()
            raise


class TransformationMiddleware(ProtocolMiddleware):
    """Middleware for data transformation.

    This middleware transforms protocol data between different formats
    or structures.
    """

    def __init__(
        self,
        transform_fn: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        """Initialize transformation middleware.

        Args:
            transform_fn: Optional transformation function

        """
        super().__init__()
        self._transform_fn = transform_fn

    async def process(
        self,
        data: Any,
        next_middleware: Callable[[Any], Any],
    ) -> Any:
        """Transform and process data.

        Args:
            data: Data to transform
            next_middleware: Next middleware in chain

        Returns:
            Any: Transformed data

        Raises:
            ValueError: If transformation fails

        """
        try:
            # Apply transformation if provided
            if self._transform_fn:
                data = self._transform_fn(data)

            return await next_middleware(data)
        except Exception as e:
            self._logger.error(f"Transformation failed: {e}")
            raise ValueError(f"Transformation failed: {e}") from e


# Export public API
__all__ = [
    "LoggingMiddleware",
    "MetricsMiddleware",
    "ProtocolMiddleware",
    "TransformationMiddleware",
    "ValidationMiddleware",
]
