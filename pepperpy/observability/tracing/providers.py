"""Trace providers for distributed tracing.

This module provides trace providers for different backends:
- Console provider for development
- Jaeger provider for production
- Zipkin provider for alternative
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

from opentelemetry.exporter.console import ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace.export import SpanExporter

logger = logging.getLogger(__name__)


class TraceProvider(ABC):
    """Base class for trace providers."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        """Initialize trace provider.

        Args:
            config: Optional provider configuration

        """
        self.config = config or {}
        self._exporter = None

    @property
    def exporter(self) -> SpanExporter:
        """Get span exporter.

        Returns:
            SpanExporter: Configured span exporter

        """
        if not self._exporter:
            self._exporter = self._create_exporter()
        return self._exporter

    @abstractmethod
    def _create_exporter(self) -> SpanExporter:
        """Create span exporter.

        Returns:
            SpanExporter: New span exporter

        """

    async def shutdown(self) -> None:
        """Shut down the provider."""
        if self._exporter:
            await self._exporter.shutdown()


class ConsoleTraceProvider(TraceProvider):
    """Console trace provider for development."""

    def _create_exporter(self) -> SpanExporter:
        """Create console span exporter.

        Returns:
            SpanExporter: Console span exporter

        """
        return ConsoleSpanExporter()


class JaegerTraceProvider(TraceProvider):
    """Jaeger trace provider for production."""

    def _create_exporter(self) -> SpanExporter:
        """Create Jaeger span exporter.

        Returns:
            SpanExporter: Jaeger span exporter

        """
        return JaegerExporter(
            agent_host_name=self.config.get("host", "localhost"),
            agent_port=self.config.get("port", 6831),
            udp_split_oversized_batches=True,
        )


class ZipkinTraceProvider(TraceProvider):
    """Zipkin trace provider for alternative."""

    def _create_exporter(self) -> SpanExporter:
        """Create Zipkin span exporter.

        Returns:
            SpanExporter: Zipkin span exporter

        """
        return ZipkinExporter(
            endpoint=self.config.get("endpoint", "http://localhost:9411/api/v2/spans"),
            local_node_ipv4=self.config.get("local_node_ipv4", "127.0.0.1"),
            local_node_port=self.config.get("local_node_port", 8080),
        )
