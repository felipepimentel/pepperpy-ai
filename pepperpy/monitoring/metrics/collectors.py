"""Metric collectors for the Pepperpy framework.

This module provides collectors for gathering metrics from various sources.
"""

import asyncio
from abc import abstractmethod

from pepperpy.core.lifecycle.base import LifecycleComponent
from pepperpy.core.models import BaseModel, Field
from pepperpy.core.types.states import ComponentState
from pepperpy.monitoring.logging import get_logger
from pepperpy.monitoring.metrics.base import Metric

# Initialize logger
logger = get_logger(__name__)


class CollectorConfig(BaseModel):
    """Configuration for a metric collector."""

    name: str = Field(description="Collector name")
    description: str = Field(default="", description="Collector description")
    interval: float = Field(default=60.0, description="Collection interval in seconds")
    labels: dict[str, str] = Field(default_factory=dict, description="Collector labels")


class MetricCollector(LifecycleComponent):
    """Base class for metric collectors."""

    def __init__(self, config: CollectorConfig) -> None:
        """Initialize the collector.

        Args:
            config: Collector configuration
        """
        super().__init__(config.name)
        self.config = config
        self._metrics: dict[str, Metric] = {}
        self._task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """Initialize the collector."""
        try:
            self._state = ComponentState.INITIALIZING
            await self._initialize_metrics()
            self._state = ComponentState.READY
            self._task = asyncio.create_task(self._collect_loop())
            self._state = ComponentState.RUNNING
            logger.info(f"Collector {self.name} initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize collector {self.name}: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up the collector."""
        try:
            self._state = ComponentState.CLEANING
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            await self._cleanup_metrics()
            self._state = ComponentState.CLEANED
            logger.info(f"Collector {self.name} cleaned up")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to cleanup collector {self.name}: {e}")
            raise

    @abstractmethod
    async def collect(self) -> None:
        """Collect metrics.

        This method should be implemented by subclasses to collect metrics
        from their specific sources.
        """
        ...

    async def _initialize_metrics(self) -> None:
        """Initialize metrics."""
        pass

    async def _cleanup_metrics(self) -> None:
        """Clean up metrics."""
        self._metrics.clear()

    async def _collect_loop(self) -> None:
        """Collection loop."""
        while True:
            try:
                await self.collect()
                await asyncio.sleep(self.config.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in collector {self.name}: {e}")
                await asyncio.sleep(1.0)


__all__ = ["CollectorConfig", "MetricCollector"]
