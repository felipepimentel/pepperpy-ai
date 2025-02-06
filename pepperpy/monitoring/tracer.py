"""Tracing functionality for the Pepperpy framework."""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import Any, TypedDict

from pepperpy.monitoring import logger


class TraceEvent(TypedDict):
    """Type definition for trace events."""

    name: str
    attributes: dict[str, Any]


class TraceSpan(TypedDict):
    """Type definition for trace spans."""

    name: str
    attributes: dict[str, Any]
    events: list[TraceEvent]


class Tracer:
    """Basic tracer implementation."""

    def __init__(self) -> None:
        """Initialize the tracer."""
        self._enabled = False
        self._current_span: TraceSpan | None = None

    @contextmanager
    def start_trace(self, name: str, **attributes: Any) -> Iterator[None]:
        """Start a new trace.

        Args:
            name: Name of the trace
            **attributes: Additional trace attributes

        Yields:
            None
        """
        if self._enabled:
            self._current_span = {
                "name": name,
                "attributes": dict(attributes),
                "events": [],
            }
            try:
                yield
            finally:
                self._current_span = None
        else:
            yield

    @asynccontextmanager
    async def start_async_trace(
        self, name: str, **attributes: Any
    ) -> AsyncIterator[None]:
        """Start a new async trace.

        Args:
            name: Name of the trace
            **attributes: Additional trace attributes

        Yields:
            None
        """
        if self._enabled:
            self._current_span = {
                "name": name,
                "attributes": dict(attributes),
                "events": [],
            }
            try:
                yield
            finally:
                self._current_span = None
        else:
            yield

    def end_trace(self) -> None:
        """End the current trace."""
        self._current_span = None

    def add_event(self, name: str, **attributes: Any) -> None:
        """Add an event to the current trace.

        Args:
            name: Name of the event
            **attributes: Additional event attributes
        """
        if self._enabled and self._current_span is not None:
            event: TraceEvent = {
                "name": name,
                "attributes": dict(attributes),
            }
            self._current_span["events"].append(event)

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the current trace.

        Args:
            key: Attribute key
            value: Attribute value
        """
        if self._enabled and self._current_span is not None:
            self._current_span["attributes"][key] = value

    @property
    def enabled(self) -> bool:
        """Whether tracing is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable tracing."""
        self._enabled = True
        logger.info("Tracing enabled")

    def disable(self) -> None:
        """Disable tracing."""
        self._enabled = False
        logger.info("Tracing disabled")


# Default tracer instance
tracer = Tracer()
