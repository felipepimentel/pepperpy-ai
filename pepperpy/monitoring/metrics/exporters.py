"""Metric exporters for the Pepperpy framework.

This module provides exporters for sending metrics to various destinations.
"""

import asyncio
import gzip
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pepperpy.core.models import BaseModel, Field
from pepperpy.core.lifecycle.base import LifecycleComponent
from pepperpy.core.types.states import ComponentState
from pepperpy.monitoring.logging import get_logger
from pepperpy.monitoring.metrics.base import Metric

# Initialize logger
logger = get_logger(__name__)


class ExporterConfig(BaseModel):
    """Configuration for a metric exporter."""

    name: str = Field(description="Exporter name")
    description: str = Field(default="", description="Exporter description")
    interval: float = Field(default=60.0, description="Export interval in seconds")
    labels: dict[str, str] = Field(default_factory=dict, description="Exporter labels")


class MetricExporter(LifecycleComponent):
    """Base class for metric exporters."""

    def __init__(self, config: ExporterConfig) -> None:
        """Initialize the exporter.

        Args:
            config: Exporter configuration
        """
        super().__init__(config.name)
        self.config = config
        self._metrics: dict[str, Metric] = {}
        self._task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """Initialize the exporter."""
        try:
            self._state = ComponentState.INITIALIZING
            await self._initialize_export()
            self._state = ComponentState.READY
            self._task = asyncio.create_task(self._export_loop())
            self._state = ComponentState.RUNNING
            logger.info(f"Exporter {self.name} initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize exporter {self.name}: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up the exporter."""
        try:
            self._state = ComponentState.CLEANING
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            await self._cleanup_export()
            self._state = ComponentState.CLEANED
            logger.info(f"Exporter {self.name} cleaned up")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to cleanup exporter {self.name}: {e}")
            raise

    @abstractmethod
    async def export(self, metrics: dict[str, Metric]) -> None:
        """Export metrics.

        This method should be implemented by subclasses to export metrics
        to their specific destinations.

        Args:
            metrics: Metrics to export
        """
        ...

    async def _initialize_export(self) -> None:
        """Initialize export."""
        pass

    async def _cleanup_export(self) -> None:
        """Clean up export."""
        self._metrics.clear()

    async def _export_loop(self) -> None:
        """Export loop."""
        while True:
            try:
                await self.export(self._metrics)
                await asyncio.sleep(self.config.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in exporter {self.name}: {e}")
                await asyncio.sleep(1.0)


class FileExporter(MetricExporter):
    """File-based metric exporter."""

    def __init__(self, config: ExporterConfig, path: Path) -> None:
        """Initialize the exporter.

        Args:
            config: Exporter configuration
            path: Export file path
        """
        super().__init__(config)
        self.path = path

    async def export(self, metrics: dict[str, Metric]) -> None:
        """Export metrics to file.

        Args:
            metrics: Metrics to export
        """
        data = {
            name: {
                "value": metric.value,
                "labels": {**metric.config.labels, **self.config.labels},
            }
            for name, metric in metrics.items()
        }

        if self.path.suffix == ".gz":
            with gzip.open(self.path, "wt") as f:
                json.dump(data, f, indent=2)
        else:
            with open(self.path, "w") as f:
                json.dump(data, f, indent=2)


__all__ = ["ExporterConfig", "FileExporter", "MetricExporter"]
