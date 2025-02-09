"""Tracing functionality for the Pepperpy framework."""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import TypedDict

from loguru import logger


class TraceAttributeValue(TypedDict, total=False):
    """Type definition for trace attribute values."""

    string_value: str
    int_value: int
    float_value: float
    bool_value: bool
    list_value: list[str | int | float]


class TraceAttributes(TypedDict, total=False):
    """Type definition for trace attributes."""

    component: str
    operation: str
    status: str
    error: str
    duration: float
    metadata: dict[str, TraceAttributeValue]


class TraceEvent(TypedDict):
    """Type definition for trace events."""

    name: str
    attributes: TraceAttributes


class TraceSpan(TypedDict):
    """Type definition for trace spans."""

    name: str
    attributes: TraceAttributes
    events: list[TraceEvent]


class Tracer:
    """Basic tracer implementation."""

    def __init__(self) -> None:
        """Initialize the tracer."""
        self._enabled = False
        self._current_span: TraceSpan | None = None

    @contextmanager
    def start_trace(
        self, name: str, **attributes: TraceAttributeValue
    ) -> Iterator[None]:
        """Start a new trace.

        Args:
            name: Name of the trace
            **attributes: Additional trace attributes defined in TraceAttributeValue

        Yields:
            None
        """
        if self._enabled:
            self._current_span = {
                "name": name,
                "attributes": {"metadata": dict(attributes)},
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
        self, name: str, **attributes: TraceAttributeValue
    ) -> AsyncIterator[None]:
        """Start a new async trace.

        Args:
            name: Name of the trace
            **attributes: Additional trace attributes defined in TraceAttributeValue

        Yields:
            None
        """
        if self._enabled:
            self._current_span = {
                "name": name,
                "attributes": {"metadata": dict(attributes)},
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

    def add_event(self, name: str, **attributes: TraceAttributeValue) -> None:
        """Add an event to the current trace.

        Args:
            name: Name of the event
            **attributes: Additional event attributes defined in TraceAttributeValue
        """
        if self._enabled and self._current_span is not None:
            event: TraceEvent = {
                "name": name,
                "attributes": {"metadata": dict(attributes)},
            }
            self._current_span["events"].append(event)

    def set_attribute(self, key: str, value: TraceAttributeValue) -> None:
        """Set an attribute on the current trace.

        Args:
            key: Attribute key
            value: Attribute value defined in TraceAttributeValue
        """
        if self._enabled and self._current_span is not None:
            if "metadata" not in self._current_span["attributes"]:
                self._current_span["attributes"]["metadata"] = {}
            self._current_span["attributes"]["metadata"][key] = value

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
