"""Metrics exporters implementation.

This module provides exporters for sending metrics:
- Base exporter interface
- File exporter
- HTTP exporter
- Custom exporters
"""

import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.monitoring.metrics.base import MetricsManager


class ExporterConfig(BaseModel):
    """Base configuration for exporters.

    Attributes:
        name: Exporter name
        enabled: Whether exporter is enabled
        interval: Export interval in seconds
        labels: Global labels to add
    """

    name: str = Field(description="Exporter name")
    enabled: bool = Field(default=True, description="Whether exporter is enabled")
    interval: float = Field(default=60.0, description="Export interval in seconds")
    labels: dict[str, str] = Field(
        default_factory=dict, description="Global labels to add"
    )


class MetricExporter(Lifecycle, ABC):
    """Base class for metric exporters.

    All exporters must implement this interface to ensure consistent
    behavior across the framework.
    """

    def __init__(self, config: ExporterConfig) -> None:
        """Initialize exporter.

        Args:
            config: Exporter configuration
        """
        super().__init__()
        self.config = config
        self._metrics_manager = MetricsManager.get_instance()
        self._state = ComponentState.UNREGISTERED
        self._export_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """Initialize exporter."""
        try:
            self._state = ComponentState.RUNNING
            if self.config.enabled:
                self._export_task = asyncio.create_task(self._export_loop())
            logger.info(f"Exporter initialized: {self.config.name}")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize exporter: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up exporter."""
        try:
            if self._export_task:
                self._export_task.cancel()
                try:
                    await self._export_task
                except asyncio.CancelledError:
                    pass
            self._state = ComponentState.UNREGISTERED
            logger.info(f"Exporter cleaned up: {self.config.name}")
        except Exception as e:
            logger.error(f"Failed to cleanup exporter: {e}")
            raise

    async def _export_loop(self) -> None:
        """Export loop."""
        while True:
            try:
                await self.export()
                await asyncio.sleep(self.config.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in export loop: {e}")
                await asyncio.sleep(1.0)  # Back off on error

    @abstractmethod
    async def export(self) -> None:
        """Export metrics.

        This method should be implemented by subclasses to export
        metrics according to their specific requirements.
        """
        pass


class FileExporter(MetricExporter):
    """Exporter that writes metrics to files.

    This exporter writes metrics to JSON files, with optional
    rotation and compression.
    """

    def __init__(
        self,
        config: ExporterConfig,
        directory: str = "metrics",
        max_files: int = 10,
        compress: bool = False,
    ) -> None:
        """Initialize file exporter.

        Args:
            config: Exporter configuration
            directory: Directory to write files to
            max_files: Maximum number of files to keep
            compress: Whether to compress files
        """
        super().__init__(config)
        self._directory = Path(directory)
        self._max_files = max_files
        self._compress = compress

    async def initialize(self) -> None:
        """Initialize exporter."""
        await super().initialize()
        self._directory.mkdir(parents=True, exist_ok=True)

    async def export(self) -> None:
        """Export metrics to file."""
        try:
            metrics = await self._metrics_manager.collect_all()
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = self._directory / f"metrics_{timestamp}.json"

            # Add global labels
            for metric in metrics:
                metric["labels"].update(self.config.labels)

            # Write metrics
            data = {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics,
            }
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)

            # Rotate files if needed
            await self._rotate_files()

            # Compress if enabled
            if self._compress:
                await self._compress_file(filename)

        except Exception as e:
            logger.error(f"Failed to export metrics to file: {e}")

    async def _rotate_files(self) -> None:
        """Rotate metric files."""
        files = sorted(self._directory.glob("metrics_*.json"))
        while len(files) > self._max_files:
            oldest = files.pop(0)
            try:
                oldest.unlink()
            except Exception as e:
                logger.error(f"Failed to delete old metric file {oldest}: {e}")

    async def _compress_file(self, file: Path) -> None:
        """Compress metric file.

        Args:
            file: File to compress
        """
        try:
            import gzip
            import shutil

            compressed = file.with_suffix(".json.gz")
            with open(file, "rb") as f_in:
                with gzip.open(compressed, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            file.unlink()
        except Exception as e:
            logger.error(f"Failed to compress metric file {file}: {e}")


class HTTPExporter(MetricExporter):
    """Exporter that sends metrics via HTTP.

    This exporter sends metrics to an HTTP endpoint in JSON format.
    """

    def __init__(
        self,
        config: ExporterConfig,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize HTTP exporter.

        Args:
            config: Exporter configuration
            url: URL to send metrics to
            headers: Optional HTTP headers
            timeout: Request timeout in seconds
        """
        super().__init__(config)
        self._url = url
        self._headers = headers or {}
        self._timeout = timeout

    async def export(self) -> None:
        """Export metrics via HTTP."""
        try:
            metrics = await self._metrics_manager.collect_all()

            # Add global labels
            for metric in metrics:
                metric["labels"].update(self.config.labels)

            # Prepare payload
            data = {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics,
            }

            # Send request
            # This is a placeholder - actual implementation would use aiohttp or similar
            logger.info(f"Would send metrics to {self._url}")
            logger.debug("Metrics payload:", extra={"metrics": data})

        except Exception as e:
            logger.error(f"Failed to export metrics via HTTP: {e}")


class ConsoleExporter(MetricExporter):
    """Exporter that prints metrics to console.

    This exporter formats metrics in a human-readable format
    and prints them to the console.
    """

    async def export(self) -> None:
        """Export metrics to console."""
        try:
            metrics = await self._metrics_manager.collect_all()

            # Add global labels
            for metric in metrics:
                metric["labels"].update(self.config.labels)

            # Print header
            print("\n=== Metrics Report ===")
            print(f"Time: {datetime.utcnow().isoformat()}")
            print("====================\n")

            # Print metrics
            for metric in metrics:
                print(f"Name: {metric['name']}")
                print(f"Type: {metric['type']}")
                print(f"Description: {metric['description']}")
                print(f"Labels: {metric['labels']}")

                if metric["type"] in ("counter", "gauge"):
                    print(f"Value: {metric['value']}")
                elif metric["type"] == "histogram":
                    print("Buckets:")
                    for bucket, count in sorted(metric["buckets"].items()):
                        print(f"  <= {bucket}: {count}")
                    print(f"Sum: {metric['sum']}")
                    print(f"Count: {metric['count']}")
                elif metric["type"] == "summary":
                    print(f"Count: {metric['count']}")
                    print(f"Sum: {metric['sum']}")

                print()

        except Exception as e:
            logger.error(f"Failed to export metrics to console: {e}")
