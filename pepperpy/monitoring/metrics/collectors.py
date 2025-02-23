"""Metrics collectors implementation.

This module provides collectors for gathering metrics:
- Base collector interface
- Prometheus collector
- OpenTelemetry collector
- Custom collectors
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.monitoring.logging import logger
from pepperpy.monitoring.metrics.base import MetricsManager


class CollectorConfig(BaseModel):
    """Base configuration for collectors.

    Attributes:
        name: Collector name
        enabled: Whether collector is enabled
        interval: Collection interval in seconds
        labels: Global labels to add
    """

    name: str = Field(description="Collector name")
    enabled: bool = Field(default=True, description="Whether collector is enabled")
    interval: float = Field(default=60.0, description="Collection interval in seconds")
    labels: dict[str, str] = Field(
        default_factory=dict, description="Global labels to add"
    )


class MetricCollector(Lifecycle, ABC):
    """Base class for metric collectors.

    All collectors must implement this interface to ensure consistent
    behavior across the framework.
    """

    def __init__(self, config: CollectorConfig) -> None:
        """Initialize collector.

        Args:
            config: Collector configuration
        """
        super().__init__()
        self.config = config
        self._metrics_manager = MetricsManager.get_instance()
        self._state = ComponentState.UNREGISTERED
        self._collection_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """Initialize collector."""
        try:
            self._state = ComponentState.RUNNING
            if self.config.enabled:
                self._collection_task = asyncio.create_task(self._collect_loop())
            logger.info(f"Collector initialized: {self.config.name}")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize collector: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up collector."""
        try:
            if self._collection_task:
                self._collection_task.cancel()
                try:
                    await self._collection_task
                except asyncio.CancelledError:
                    pass
            self._state = ComponentState.UNREGISTERED
            logger.info(f"Collector cleaned up: {self.config.name}")
        except Exception as e:
            logger.error(f"Failed to cleanup collector: {e}")
            raise

    async def _collect_loop(self) -> None:
        """Collection loop."""
        while True:
            try:
                await self.collect()
                await asyncio.sleep(self.config.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(1.0)  # Back off on error

    @abstractmethod
    async def collect(self) -> None:
        """Collect metrics.

        This method should be implemented by subclasses to collect
        and process metrics according to their specific requirements.
        """
        pass


class PrometheusCollector(MetricCollector):
    """Collector for Prometheus metrics.

    This collector formats metrics in Prometheus text format
    and exposes them via HTTP endpoint.
    """

    def __init__(
        self,
        config: CollectorConfig,
        endpoint: str = "/metrics",
        port: int = 9090,
    ) -> None:
        """Initialize Prometheus collector.

        Args:
            config: Collector configuration
            endpoint: HTTP endpoint for metrics
            port: HTTP port for metrics server
        """
        super().__init__(config)
        self._endpoint = endpoint
        self._port = port
        self._server: Any | None = None  # Type depends on HTTP server implementation

    async def initialize(self) -> None:
        """Initialize collector."""
        await super().initialize()
        # Start HTTP server here
        # This is a placeholder - actual implementation would use aiohttp or similar

    async def cleanup(self) -> None:
        """Clean up collector."""
        if self._server:
            # Stop HTTP server here
            pass
        await super().cleanup()

    async def collect(self) -> None:
        """Collect and format metrics."""
        try:
            metrics = await self._metrics_manager.collect_all()
            formatted = self._format_metrics(metrics)
            # Update HTTP endpoint with formatted metrics
            # This is a placeholder - actual implementation would update server
        except Exception as e:
            logger.error(f"Failed to collect Prometheus metrics: {e}")

    def _format_metrics(self, metrics: list[dict[str, Any]]) -> str:
        """Format metrics in Prometheus text format.

        Args:
            metrics: List of metric data

        Returns:
            Formatted metrics string
        """
        lines = []
        for metric in metrics:
            # Add metric metadata
            lines.append(f"# HELP {metric['name']} {metric['description']}")
            lines.append(f"# TYPE {metric['name']} {metric['type']}")

            # Format value based on type
            if metric["type"] == "counter":
                lines.append(self._format_simple_metric(metric))
            elif metric["type"] == "gauge":
                lines.append(self._format_simple_metric(metric))
            elif metric["type"] == "histogram":
                lines.extend(self._format_histogram_metric(metric))
            elif metric["type"] == "summary":
                lines.extend(self._format_summary_metric(metric))

        return "\n".join(lines)

    def _format_simple_metric(self, metric: dict[str, Any]) -> str:
        """Format simple metric (counter/gauge).

        Args:
            metric: Metric data

        Returns:
            Formatted metric string
        """
        labels = self._format_labels({**self.config.labels, **metric["labels"]})
        return f"{metric['name']}{labels} {metric['value']}"

    def _format_histogram_metric(self, metric: dict[str, Any]) -> list[str]:
        """Format histogram metric.

        Args:
            metric: Metric data

        Returns:
            List of formatted metric strings
        """
        lines = []
        name = metric["name"]
        labels = self._format_labels({**self.config.labels, **metric["labels"]})

        # Add bucket values
        acc = 0
        for bucket, count in sorted(metric["buckets"].items()):
            acc += count
            bucket_labels = self._format_labels({
                **self.config.labels,
                **metric["labels"],
                "le": str(bucket),
            })
            lines.append(f"{name}_bucket{bucket_labels} {acc}")

        # Add sum and count
        lines.append(f"{name}_sum{labels} {metric['sum']}")
        lines.append(f"{name}_count{labels} {metric['count']}")

        return lines

    def _format_summary_metric(self, metric: dict[str, Any]) -> list[str]:
        """Format summary metric.

        Args:
            metric: Metric data

        Returns:
            List of formatted metric strings
        """
        lines = []
        name = metric["name"]
        labels = self._format_labels({**self.config.labels, **metric["labels"]})

        # Add sum and count
        lines.append(f"{name}_sum{labels} {metric['sum']}")
        lines.append(f"{name}_count{labels} {metric['count']}")

        return lines

    def _format_labels(self, labels: dict[str, str]) -> str:
        """Format metric labels.

        Args:
            labels: Label dictionary

        Returns:
            Formatted labels string
        """
        if not labels:
            return ""
        label_pairs = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return "{" + ",".join(label_pairs) + "}"


class OpenTelemetryCollector(MetricCollector):
    """Collector for OpenTelemetry metrics.

    This collector exports metrics to OpenTelemetry collectors
    using the OpenTelemetry SDK.
    """

    def __init__(
        self,
        config: CollectorConfig,
        endpoint: str = "localhost:4317",
        insecure: bool = False,
    ) -> None:
        """Initialize OpenTelemetry collector.

        Args:
            config: Collector configuration
            endpoint: OpenTelemetry collector endpoint
            insecure: Whether to use insecure connection
        """
        super().__init__(config)
        self._endpoint = endpoint
        self._insecure = insecure
        self._exporter: Any | None = None  # Type depends on OTel implementation

    async def initialize(self) -> None:
        """Initialize collector."""
        await super().initialize()
        # Initialize OpenTelemetry exporter here
        # This is a placeholder - actual implementation would use opentelemetry-sdk

    async def cleanup(self) -> None:
        """Clean up collector."""
        if self._exporter:
            # Shutdown exporter here
            pass
        await super().cleanup()

    async def collect(self) -> None:
        """Collect and export metrics."""
        try:
            metrics = await self._metrics_manager.collect_all()
            # Export metrics using OpenTelemetry SDK
            # This is a placeholder - actual implementation would use OTel SDK
        except Exception as e:
            logger.error(f"Failed to collect OpenTelemetry metrics: {e}")


class LoggingCollector(MetricCollector):
    """Collector that logs metrics.

    This collector writes metrics to the logging system,
    useful for debugging and development.
    """

    async def collect(self) -> None:
        """Collect and log metrics."""
        try:
            metrics = await self._metrics_manager.collect_all()
            for metric in metrics:
                logger.info(
                    f"Metric: {metric['name']}",
                    extra={
                        "metric_type": metric["type"],
                        "metric_value": metric.get("value"),
                        "metric_labels": metric["labels"],
                        "metric_timestamp": metric["timestamp"],
                    },
                )
        except Exception as e:
            logger.error(f"Failed to collect logging metrics: {e}")
