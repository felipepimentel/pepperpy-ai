"""Monitoring manager for the Pepperpy framework.

This module provides the monitoring manager that coordinates monitoring functionality.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from pepperpy.core.base import BaseComponent
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.monitoring.alerts import AlertManager
from pepperpy.core.monitoring.collector import MonitoringCollector
from pepperpy.core.monitoring.errors import (
    CollectorError,
    ValidationError,
)
from pepperpy.core.monitoring.exporters.base import MonitoringExporter
from pepperpy.core.monitoring.types import (
    Alert,
    AlertSeverity,
    AlertState,
    MonitoringEvent,
    MonitoringLevel,
    MonitoringMetric,
    MonitoringRule,
)


class MonitoringManager(BaseComponent, LifecycleComponent):
    """Manager for monitoring functionality."""

    def __init__(
        self,
        name: str = "monitoring_manager",
        export_interval: float = 60.0,
    ) -> None:
        """Initialize monitoring manager.

        Args:
            name: Manager name
            export_interval: Export interval in seconds
        """
        super().__init__(name)
        self._export_interval = export_interval
        self._exporters: list[MonitoringExporter] = []
        self._collectors: list[MonitoringCollector] = []
        self._alert_manager = AlertManager()
        self._export_task: asyncio.Task[None] | None = None

    async def initialize(self) -> None:
        """Initialize monitoring manager.

        Raises:
            ValidationError: If initialization fails
        """
        try:
            await self._initialize()
        except Exception as e:
            raise ValidationError(f"Failed to initialize monitoring manager: {e}")

    async def cleanup(self) -> None:
        """Clean up monitoring manager.

        Raises:
            ValidationError: If cleanup fails
        """
        try:
            await self._cleanup()
        except Exception as e:
            raise ValidationError(f"Failed to clean up monitoring manager: {e}")

    async def _initialize(self) -> None:
        """Initialize monitoring manager implementation."""
        # Initialize alert manager
        await self._alert_manager.initialize()

        # Initialize collectors
        for collector in self._collectors:
            await collector.initialize()

        # Initialize exporters
        for exporter in self._exporters:
            await exporter.initialize()

        # Start export loop
        self._export_task = asyncio.create_task(self._export_loop())

    async def _cleanup(self) -> None:
        """Clean up monitoring manager implementation."""
        # Stop export loop
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass

        # Clean up exporters
        for exporter in self._exporters:
            await exporter.cleanup()

        # Clean up collectors
        for collector in self._collectors:
            await collector.cleanup()

        # Clean up alert manager
        await self._alert_manager.cleanup()

    def add_exporter(self, exporter: MonitoringExporter) -> None:
        """Add monitoring exporter.

        Args:
            exporter: Exporter to add
        """
        self._exporters.append(exporter)

    def remove_exporter(self, exporter: MonitoringExporter) -> None:
        """Remove monitoring exporter.

        Args:
            exporter: Exporter to remove
        """
        self._exporters.remove(exporter)

    async def record_event(
        self,
        level: MonitoringLevel,
        source: str,
        message: str,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record monitoring event.

        Args:
            level: Event level
            source: Event source
            message: Event message
            data: Optional event data
            metadata: Optional event metadata

        Raises:
            ValidationError: If event is invalid
        """
        try:
            event = MonitoringEvent(
                level=level,
                source=source,
                message=message,
                data=data or {},
                metadata=metadata or {},
            )

            # Export event
            for exporter in self._exporters:
                await exporter.export_events([event])

        except Exception as e:
            raise ValidationError(f"Failed to record event: {e}")

    async def record_metric(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record monitoring metric.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional metric labels
            metadata: Optional metric metadata

        Raises:
            ValidationError: If metric is invalid
        """
        try:
            metric = MonitoringMetric(
                name=name,
                value=value,
                labels=labels or {},
                metadata=metadata or {},
            )

            # Export metric
            for exporter in self._exporters:
                await exporter.export_metrics([metric])

        except Exception as e:
            raise ValidationError(f"Failed to record metric: {e}")

    async def add_rule(self, rule: MonitoringRule) -> None:
        """Add monitoring rule.

        Args:
            rule: Rule to add

        Raises:
            ValidationError: If rule is invalid
        """
        try:
            await self._alert_manager.add_rule(rule)
        except Exception as e:
            raise ValidationError(f"Failed to add rule: {e}")

    async def remove_rule(self, rule_id: str) -> None:
        """Remove monitoring rule.

        Args:
            rule_id: ID of rule to remove

        Raises:
            ValidationError: If rule not found
        """
        try:
            await self._alert_manager.remove_rule(rule_id)
        except Exception as e:
            raise ValidationError(f"Failed to remove rule: {e}")

    async def get_alerts(
        self,
        severity: AlertSeverity | None = None,
        state: AlertState | None = None,
        source: str | None = None,
    ) -> list[Alert]:
        """Get alerts matching criteria.

        Args:
            severity: Optional severity filter
            state: Optional state filter
            source: Optional source filter

        Returns:
            list[Alert]: Matching alerts
        """
        return await self._alert_manager.get_alerts(severity, state, source)

    async def update_alert(
        self,
        alert_id: str,
        state: AlertState | None = None,
        annotations: dict[str, str] | None = None,
    ) -> None:
        """Update alert.

        Args:
            alert_id: Alert ID
            state: Optional new state
            annotations: Optional annotations to update

        Raises:
            ValidationError: If alert not found
        """
        try:
            await self._alert_manager.update_alert(alert_id, state, annotations)
        except Exception as e:
            raise ValidationError(f"Failed to update alert: {e}")

    async def get_events(
        self,
        level: MonitoringLevel | None = None,
        source: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[MonitoringEvent]:
        """Get monitoring events.

        Args:
            level: Optional level filter
            source: Optional source filter
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            list[MonitoringEvent]: Matching events
        """
        events: list[MonitoringEvent] = []
        for collector in self._collectors:
            try:
                async for event in await collector.collect_events():
                    if level and event.level != level:
                        continue
                    if source and event.source != source:
                        continue
                    if start_time and event.timestamp < start_time:
                        continue
                    if end_time and event.timestamp > end_time:
                        continue
                    events.append(event)
            except Exception as e:
                raise CollectorError(f"Failed to collect events: {e}")
        return events

    async def get_metrics(
        self,
        name: str | None = None,
        labels: dict[str, str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[MonitoringMetric]:
        """Get monitoring metrics.

        Args:
            name: Optional name filter
            labels: Optional labels filter
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            list[MonitoringMetric]: Matching metrics
        """
        metrics: list[MonitoringMetric] = []
        for collector in self._collectors:
            try:
                async for metric in await collector.collect_metrics():
                    if name and metric.name != name:
                        continue
                    if labels and not all(
                        metric.labels.get(k) == v for k, v in labels.items()
                    ):
                        continue
                    if start_time and metric.timestamp < start_time:
                        continue
                    if end_time and metric.timestamp > end_time:
                        continue
                    metrics.append(metric)
            except Exception as e:
                raise CollectorError(f"Failed to collect metrics: {e}")
        return metrics

    async def _export_loop(self) -> None:
        """Export loop for monitoring data."""
        while True:
            try:
                # Collect and export events
                events = await self.get_events()
                for exporter in self._exporters:
                    await exporter.export_events(events)

                # Collect and export metrics
                metrics = await self.get_metrics()
                for exporter in self._exporters:
                    await exporter.export_metrics(metrics)

                # Wait for next export
                await asyncio.sleep(self._export_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Export loop failed: {e}")
                await asyncio.sleep(1.0)


__all__ = ["MonitoringManager"]
