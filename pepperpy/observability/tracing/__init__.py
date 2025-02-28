"""Distributed tracing module for Pepperpy.

This module provides distributed tracing capabilities:
- OpenTelemetry integration
- Context propagation
- Span management
- Trace sampling
- Trace export
"""

import logging
from typing import Dict, Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
from opentelemetry.trace import Status, StatusCode

from pepperpy.common.base import Lifecycle
from pepperpy.core.types import ComponentState

from .context import TraceContext
from .providers import (
    ConsoleTraceProvider,
    JaegerTraceProvider,
    ZipkinTraceProvider,
)

logger = logging.getLogger(__name__)


class TracingManager(Lifecycle):
    """Manages distributed tracing."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        """Initialize tracing manager.

        Args:
            config: Optional tracing configuration
        """
        super().__init__()
        self.config = config or {}
        self._provider = None
        self._tracer = None
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize tracing system.

        This sets up the tracer provider and processors.
        """
        try:
            # Set up provider
            provider_type = self.config.get("provider", "console")
            if provider_type == "jaeger":
                self._provider = JaegerTraceProvider(self.config)
            elif provider_type == "zipkin":
                self._provider = ZipkinTraceProvider(self.config)
            else:
                self._provider = ConsoleTraceProvider(self.config)

            # Configure sampling
            sampler = ParentBasedTraceIdRatio(
                root_sampler=self.config.get("sampling_ratio", 1.0)
            )
            trace.set_tracer_provider(TracerProvider(sampler=sampler))

            # Set up processor
            processor = BatchSpanProcessor(self._provider.exporter)
            trace.get_tracer_provider().add_span_processor(processor)

            # Get tracer
            self._tracer = trace.get_tracer(__name__)
            self._state = ComponentState.RUNNING

            logger.info("Tracing system initialized")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize tracing: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up tracing system."""
        try:
            if self._provider:
                await self._provider.shutdown()
            self._state = ComponentState.UNREGISTERED
            logger.info("Tracing system cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup tracing: {e}")
            raise

    def start_span(
        self, name: str, context: Optional[TraceContext] = None
    ) -> TraceContext:
        """Start a new span.

        Args:
            name: Name of the span
            context: Optional parent context

        Returns:
            TraceContext: New trace context
        """
        parent_context = context.context if context else None
        span = self._tracer.start_span(name, context=parent_context)
        return TraceContext(span)

    def end_span(self, context: TraceContext, status: Optional[str] = None) -> None:
        """End a span.

        Args:
            context: Trace context to end
            status: Optional status message
        """
        if status:
            context.span.set_status(Status(StatusCode.OK))
        context.span.end()
