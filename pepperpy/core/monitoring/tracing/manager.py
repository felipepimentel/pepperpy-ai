"""Manager for distributed tracing."""

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List, Optional, Set

from pepperpy.core.lifecycle import Lifecycle

from .types import Span, SpanContext, SpanKind, SpanStatus


class TracingManager(Lifecycle):
    """Central manager for distributed tracing.

    This class manages trace creation and correlation.
    It supports span creation, context propagation, and sampling.

    Attributes:
        active_spans: Currently active spans

    """

    def __init__(self) -> None:
        """Initialize the manager."""
        super().__init__()
        self._spans: Dict[str, Span] = {}
        self._active_traces: Set[str] = set()
        self._lock = asyncio.Lock()
        self._sampling_rate = 1.0  # Sample all traces by default

    def set_sampling_rate(self, rate: float) -> None:
        """Set the sampling rate.

        Args:
            rate: Sampling rate (0.0 to 1.0)

        Raises:
            ValueError: If rate is invalid

        """
        if not 0.0 <= rate <= 1.0:
            raise ValueError("Sampling rate must be between 0.0 and 1.0")
        self._sampling_rate = rate

    def _generate_id(self) -> str:
        """Generate a unique identifier.

        Returns:
            Unique identifier string

        """
        return str(uuid.uuid4())

    def _should_sample(self) -> bool:
        """Check if a trace should be sampled.

        Returns:
            True if the trace should be sampled

        """
        import random

        return random.random() < self._sampling_rate

    async def create_span(
        self,
        name: str,
        parent_context: Optional[SpanContext] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        **attributes: str,
    ) -> Span:
        """Create a new span.

        Args:
            name: Span name
            parent_context: Optional parent span context
            kind: Span kind
            **attributes: Span attributes

        Returns:
            Created span

        """
        async with self._lock:
            span_id = self._generate_id()
            trace_id = (
                parent_context.trace_id if parent_context else self._generate_id()
            )

            # Create span context
            context = SpanContext(
                trace_id=trace_id,
                span_id=span_id,
                parent_id=parent_context.span_id if parent_context else None,
                sampled=parent_context.sampled
                if parent_context
                else self._should_sample(),
            )

            # Create span
            span = Span(
                name=name,
                context=context,
                kind=kind,
                start_time=None,  # Set when span is started
                end_time=None,  # Set when span is ended
                attributes=attributes,
                events=[],
                status=SpanStatus.UNSET,
            )

            self._spans[span_id] = span
            if not parent_context:
                self._active_traces.add(trace_id)

            return span

    @asynccontextmanager
    async def span(
        self,
        name: str,
        parent_context: Optional[SpanContext] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        **attributes: str,
    ) -> AsyncGenerator[Span, None]:
        """Create and manage a span using a context manager.

        Args:
            name: Span name
            parent_context: Optional parent span context
            kind: Span kind
            **attributes: Span attributes

        Yields:
            Active span

        """
        span = await self.create_span(name, parent_context, kind, **attributes)
        try:
            span.start()
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(SpanStatus.ERROR)
            raise
        finally:
            span.end()
            await self._export_span(span)

    async def _export_span(self, span: Span) -> None:
        """Export a completed span.

        Args:
            span: Span to export

        """
        # Remove from active spans
        async with self._lock:
            self._spans.pop(span.context.span_id, None)
            if not span.context.parent_id:
                self._active_traces.discard(span.context.trace_id)

    async def get_active_spans(self) -> List[Span]:
        """Get all currently active spans.

        Returns:
            List of active spans

        """
        async with self._lock:
            return list(self._spans.values())

    async def initialize(self) -> None:
        """Initialize the manager."""
        # Nothing to initialize yet
        pass

    async def cleanup(self) -> None:
        """Clean up the manager.

        This ends all active spans and clears all state.
        """
        # End all active spans
        active_spans = await self.get_active_spans()
        for span in active_spans:
            if not span.end_time:
                span.end()
                await self._export_span(span)

        # Clear state
        async with self._lock:
            self._spans.clear()
            self._active_traces.clear()
