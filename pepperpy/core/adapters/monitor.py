"""Adapter monitor system.

This module provides adapter monitoring functionality:
- Adapter usage tracking
- Adapter metrics collection
- Adapter analysis
- Adapter alerts
"""

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any

from pepperpy.core.adapters.base import (
    Adapter,
    AdapterState,
    AdapterType,
)
from pepperpy.core.errors import AdapterError
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)


class AdapterUsage:
    """Adapter usage information."""

    def __init__(self) -> None:
        """Initialize usage tracker."""
        self.total_adaptations = 0
        self.total_failures = 0
        self.active_adapters = 0
        self.error_count = 0
        self.last_error: str | None = None
        self.last_adaptation: datetime | None = None
        self.last_failure: datetime | None = None

    def record_adaptation(self) -> None:
        """Record successful adaptation."""
        self.total_adaptations += 1
        self.last_adaptation = datetime.utcnow()

    def record_failure(self, error: str) -> None:
        """Record adaptation failure.

        Args:
            error: Error message
        """
        self.total_failures += 1
        self.error_count += 1
        self.last_error = error
        self.last_failure = datetime.utcnow()


class AdapterMonitor(LifecycleComponent):
    """Monitor for adapter usage."""

    def __init__(self, name: str) -> None:
        """Initialize monitor.

        Args:
            name: Monitor name
        """
        super().__init__(name)
        self._usage: dict[AdapterType, AdapterUsage] = defaultdict(AdapterUsage)
        self._adapters: dict[str, Adapter[Any, Any]] = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize monitor.

        Raises:
            AdapterError: If initialization fails
        """
        try:
            await super().initialize()
            logger.info("Adapter monitor initialized", extra={"name": self.name})
        except Exception as e:
            raise AdapterError(f"Failed to initialize adapter monitor: {e}")

    async def cleanup(self) -> None:
        """Clean up monitor.

        Raises:
            AdapterError: If cleanup fails
        """
        try:
            await super().cleanup()
            async with self._lock:
                self._usage.clear()
                self._adapters.clear()
            logger.info("Adapter monitor cleaned up", extra={"name": self.name})
        except Exception as e:
            raise AdapterError(f"Failed to clean up adapter monitor: {e}")

    async def track_adapter(self, adapter: Adapter[Any, Any]) -> None:
        """Track adapter usage.

        Args:
            adapter: Adapter to track

        Raises:
            AdapterError: If tracking fails
        """
        try:
            async with self._lock:
                self._adapters[adapter.name] = adapter
                usage = self._usage[adapter.get_metadata().type]
                usage.active_adapters += 1

                logger.info(
                    "Started tracking adapter",
                    extra={
                        "name": adapter.name,
                        "type": adapter.get_metadata().type,
                    },
                )

        except Exception as e:
            raise AdapterError(f"Failed to track adapter: {e}")

    async def untrack_adapter(self, adapter: Adapter[Any, Any]) -> None:
        """Stop tracking adapter usage.

        Args:
            adapter: Adapter to untrack

        Raises:
            AdapterError: If untracking fails
        """
        try:
            async with self._lock:
                if adapter.name in self._adapters:
                    del self._adapters[adapter.name]
                    usage = self._usage[adapter.get_metadata().type]
                    usage.active_adapters -= 1

                    logger.info(
                        "Stopped tracking adapter",
                        extra={
                            "name": adapter.name,
                            "type": adapter.get_metadata().type,
                        },
                    )

        except Exception as e:
            raise AdapterError(f"Failed to untrack adapter: {e}")

    async def record_adaptation(self, adapter: Adapter[Any, Any]) -> None:
        """Record successful adaptation.

        Args:
            adapter: Adapter that performed adaptation

        Raises:
            AdapterError: If recording fails
        """
        try:
            async with self._lock:
                usage = self._usage[adapter.get_metadata().type]
                usage.record_adaptation()

                logger.info(
                    "Recorded adaptation",
                    extra={
                        "name": adapter.name,
                        "type": adapter.get_metadata().type,
                    },
                )

        except Exception as e:
            raise AdapterError(f"Failed to record adaptation: {e}")

    async def record_failure(self, adapter: Adapter[Any, Any], error: str) -> None:
        """Record adaptation failure.

        Args:
            adapter: Adapter that failed
            error: Error message

        Raises:
            AdapterError: If recording fails
        """
        try:
            async with self._lock:
                usage = self._usage[adapter.get_metadata().type]
                usage.record_failure(error)

                logger.error(
                    "Adapter failure",
                    extra={
                        "name": adapter.name,
                        "type": adapter.get_metadata().type,
                        "error": error,
                    },
                )

        except Exception as e:
            raise AdapterError(f"Failed to record failure: {e}")

    def get_usage(self, type: AdapterType | None = None) -> dict[str, Any]:
        """Get adapter usage statistics.

        Args:
            type: Optional adapter type filter

        Returns:
            Usage statistics
        """
        stats: dict[str, Any] = {
            "total_adapters": len(self._adapters),
            "by_type": {},
            "by_state": defaultdict(int),
        }

        # Collect type stats
        for adapter_type, usage in self._usage.items():
            if type and adapter_type != type:
                continue

            stats["by_type"][adapter_type] = {
                "total_adaptations": usage.total_adaptations,
                "total_failures": usage.total_failures,
                "active_adapters": usage.active_adapters,
                "error_count": usage.error_count,
                "last_error": usage.last_error,
                "last_adaptation": usage.last_adaptation,
                "last_failure": usage.last_failure,
            }

        # Collect state stats
        for adapter in self._adapters.values():
            if type and adapter.get_metadata().type != type:
                continue
            stats["by_state"][adapter.state] += 1

        return stats

    def get_active_adapters(
        self,
        type: AdapterType | None = None,
    ) -> list[Adapter[Any, Any]]:
        """Get active adapters.

        Args:
            type: Optional adapter type filter

        Returns:
            List of active adapters
        """
        adapters = [a for a in self._adapters.values() if a.state == AdapterState.READY]

        if type:
            adapters = [a for a in adapters if a.get_metadata().type == type]

        return adapters


# Global adapter monitor instance
adapter_monitor = AdapterMonitor("global")


# Export public API
__all__ = [
    "AdapterMonitor",
    "AdapterUsage",
    "adapter_monitor",
]
