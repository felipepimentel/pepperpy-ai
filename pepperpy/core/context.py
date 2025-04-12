"""
PepperPy Execution Context Module.

Provides a context object that flows through the entire request lifecycle.
"""

import asyncio
import contextvars
import time
import uuid
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from pepperpy.core.base import PepperpyError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


class ContextError(PepperpyError):
    """Error related to execution context."""

    pass


# Context variable to store the current execution context
_current_context = contextvars.ContextVar("current_context", default=None)


class ExecutionContext:
    """Context for a single request execution.

    Provides context that flows through the entire request lifecycle.
    Supports tracing, metrics, and other cross-cutting concerns.
    """

    def __init__(
        self,
        request_id: str | None = None,
        tenant_id: str | None = None,
        parent_id: str | None = None,
    ) -> None:
        """Initialize execution context.

        Args:
            request_id: Unique identifier for this request
            tenant_id: Identifier for the tenant
            parent_id: Identifier for parent request if this is a sub-request
        """
        self.request_id = request_id or str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.parent_id = parent_id
        self.start_time = time.time()
        self.metadata: dict[str, Any] = {}
        self.attributes: dict[str, Any] = {}
        self.span_ids: list[str] = []
        self.token = None  # Token for context var

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the context.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the context.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute in the context.

        Attributes are mutable and can be updated throughout the request.

        Args:
            key: Attribute key
            value: Attribute value
        """
        self.attributes[key] = value

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get an attribute from the context.

        Args:
            key: Attribute key
            default: Default value if key not found

        Returns:
            Attribute value or default
        """
        return self.attributes.get(key, default)

    def start_span(self, name: str) -> str:
        """Start a new span for tracing.

        Args:
            name: Span name

        Returns:
            Span ID
        """
        span_id = f"{name}_{uuid.uuid4()}"
        self.span_ids.append(span_id)
        logger.debug(f"Starting span: {name} ({span_id})")
        return span_id

    def end_span(self, span_id: str) -> None:
        """End a span.

        Args:
            span_id: Span ID to end
        """
        if span_id in self.span_ids:
            self.span_ids.remove(span_id)
            logger.debug(f"Ending span: {span_id}")

    def get_elapsed_time(self) -> float:
        """Get elapsed time since context creation.

        Returns:
            Elapsed time in seconds
        """
        return time.time() - self.start_time

    def activate(self) -> None:
        """Activate this context in the current execution flow."""
        self.token = _current_context.set(self)  # type: ignore

    def deactivate(self) -> None:
        """Deactivate this context in the current execution flow."""
        if self.token:
            _current_context.reset(self.token)
            self.token = None


def get_current_context() -> ExecutionContext | None:
    """Get the current execution context.

    Returns:
        Current execution context or None if not in a context
    """
    return _current_context.get()


@asynccontextmanager
async def execution_context(
    request_id: str | None = None,
    tenant_id: str | None = None,
    parent_id: str | None = None,
) -> AsyncGenerator[ExecutionContext, None]:
    """Context manager for execution context.

    Args:
        request_id: Unique identifier for this request
        tenant_id: Identifier for the tenant
        parent_id: Identifier for parent request if this is a sub-request

    Yields:
        Execution context
    """
    context = ExecutionContext(
        request_id=request_id,
        tenant_id=tenant_id,
        parent_id=parent_id,
    )

    try:
        # Activate context
        context.activate()

        # Yield context to caller
        yield context
    finally:
        # Deactivate context
        context.deactivate()


async def with_context(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Run a function with a new execution context.

    Args:
        func: Function to run
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Function result
    """
    async with execution_context() as context:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
