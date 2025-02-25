"""Prometheus exporter for monitoring metrics and events."""

from typing import Any

from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram
from prometheus_client.exposition import generate_latest

from pepperpy.core.monitoring.base import MonitoringExporter
from pepperpy.core.monitoring.errors import ExporterError


class PrometheusExporter(MonitoringExporter):
    """Prometheus exporter for monitoring metrics and events."""

    def __init__(
        self,
        name: str = "prometheus",
        host: str = "localhost",
        port: int = 9090,
        path: str = "/metrics",
    ) -> None:
        """Initialize the Prometheus exporter.

        Args:
            name: The name of the exporter.
            host: The host to bind to.
            port: The port to bind to.
            path: The path to expose metrics on.
        """
        super().__init__(name)
        self.host = host
        self.port = port
        self.path = path
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._metrics: dict[str, Counter | Gauge | Histogram] = {}

    async def _initialize(self) -> None:
        """Initialize the Prometheus exporter."""
        try:
            self._app = web.Application()
            self._app.router.add_get(self.path, self._handle_metrics)
            self._runner = web.AppRunner(self._app)
            await self._runner.setup()
            self._site = web.TCPSite(self._runner, self.host, self.port)
            await self._site.start()
        except Exception as e:
            raise ExporterError(f"Failed to initialize Prometheus exporter: {e}") from e

    async def _cleanup(self) -> None:
        """Clean up the Prometheus exporter."""
        try:
            if self._site:
                await self._site.stop()
            if self._runner:
                await self._runner.cleanup()
        except Exception as e:
            raise ExporterError(f"Failed to clean up Prometheus exporter: {e}") from e

    async def _handle_metrics(self, request: web.Request) -> web.Response:
        """Handle metrics requests.

        Args:
            request: The incoming request.

        Returns:
            The response containing the metrics.
        """
        try:
            return web.Response(
                body=generate_latest(),
                content_type=CONTENT_TYPE_LATEST,
            )
        except Exception as e:
            raise ExporterError(f"Failed to handle metrics request: {e}") from e

    async def export_events(self, events: list[dict[str, Any]]) -> None:
        """Export events to Prometheus.

        Args:
            events: The events to export.
        """
        try:
            for event in events:
                metric_name = f"event_{event['name']}"
                if metric_name not in self._metrics:
                    self._metrics[metric_name] = Counter(
                        metric_name,
                        event.get("description", f"Event counter for {event['name']}"),
                        event.get("labels", []),
                    )
                self._metrics[metric_name].inc()
        except Exception as e:
            raise ExporterError(f"Failed to export events: {e}") from e

    async def export_metrics(self, metrics: list[dict[str, Any]]) -> None:
        """Export metrics to Prometheus.

        Args:
            metrics: The metrics to export.
        """
        try:
            for metric in metrics:
                metric_name = metric["name"]
                if metric_name not in self._metrics:
                    metric_type = metric.get("type", "gauge").lower()
                    if metric_type == "counter":
                        self._metrics[metric_name] = Counter(
                            metric_name,
                            metric.get("description", f"Counter for {metric_name}"),
                            metric.get("labels", []),
                        )
                    elif metric_type == "gauge":
                        self._metrics[metric_name] = Gauge(
                            metric_name,
                            metric.get("description", f"Gauge for {metric_name}"),
                            metric.get("labels", []),
                        )
                    elif metric_type == "histogram":
                        self._metrics[metric_name] = Histogram(
                            metric_name,
                            metric.get("description", f"Histogram for {metric_name}"),
                            metric.get("labels", []),
                            buckets=metric.get("buckets", None),
                        )
                    else:
                        raise ExporterError(f"Unsupported metric type: {metric_type}")

                value = metric.get("value", 0)
                labels = metric.get("labels", {})
                if isinstance(self._metrics[metric_name], Counter):
                    self._metrics[metric_name].inc(value)
                elif isinstance(self._metrics[metric_name], Gauge):
                    self._metrics[metric_name].set(value)
                elif isinstance(self._metrics[metric_name], Histogram):
                    self._metrics[metric_name].observe(value)
        except Exception as e:
            raise ExporterError(f"Failed to export metrics: {e}") from e


# Export public API
__all__ = ["PrometheusExporter"]
