"""Performance monitoring dashboard for runtime components.

This module provides functionality for tracking and visualizing performance metrics,
including agent performance, resource utilization, and system health indicators.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel

from pepperpy.core.protocols import MetricType
from pepperpy.core.types import AgentState
from pepperpy.monitoring import logger, metrics
from pepperpy.monitoring.decorators import with_trace

T = TypeVar("T")


class DashboardConfig(BaseModel):
    """Configuration for the monitoring dashboard."""

    snapshot_retention_seconds: int = 3600  # Keep snapshots for 1 hour
    warning_threshold: float = 0.8  # 80% of threshold
    alert_threshold: float = 0.95  # 95% of threshold


class MetricDefinition(BaseModel):
    """Definition of a metric to track."""

    name: str
    description: str
    unit: str
    warning_threshold: float | None = None
    alert_threshold: float | None = None


@dataclass
class MetricSnapshot:
    """Snapshot of metric values at a point in time."""

    timestamp: datetime
    values: dict[str, float]
    metadata: dict[str, str]


class MonitoringDashboard:
    """Dashboard for monitoring system performance."""

    def __init__(self, config: DashboardConfig) -> None:
        """Initialize the monitoring dashboard.

        Args:
            config: Dashboard configuration
        """
        self.config = config
        self._metrics: dict[str, MetricDefinition] = {}
        self._snapshots: dict[UUID, list[MetricSnapshot]] = {}

    @with_trace("register_metric")
    def register_metric(self, metric: MetricDefinition) -> None:
        """Register a new metric to track.

        Args:
            metric: Definition of the metric
        """
        self._metrics[metric.name] = metric
        logger.info("Registered new metric", metric_name=metric.name)

    @with_trace("record_metrics")
    async def record_metrics(self, agent_id: UUID, values: dict[str, float]) -> None:
        """Record metric values for an agent.

        Args:
            agent_id: ID of the agent
            values: Dictionary of metric values
        """
        snapshot = MetricSnapshot(
            timestamp=datetime.utcnow(),
            values=values,
            metadata={"agent_id": str(agent_id)},
        )

        if agent_id not in self._snapshots:
            self._snapshots[agent_id] = []

        self._snapshots[agent_id].append(snapshot)
        self._check_thresholds(agent_id, values)

        # Record metrics in monitoring system
        for name, value in values.items():
            metrics.record_metric(
                name=name,
                value=value,
                type=MetricType.GAUGE,
                labels={"agent_id": str(agent_id)},
            )

    def _check_thresholds(self, agent_id: UUID, values: dict[str, float]) -> None:
        """Check metric values against thresholds.

        Args:
            agent_id: ID of the agent
            values: Dictionary of metric values
        """
        for name, value in values.items():
            if name not in self._metrics:
                continue

            metric = self._metrics[name]
            if metric.warning_threshold and value > metric.warning_threshold:
                logger.warning(
                    "Metric exceeded warning threshold",
                    metric_name=name,
                    agent_id=str(agent_id),
                    value=value,
                    threshold=metric.warning_threshold,
                )

            if metric.alert_threshold and value > metric.alert_threshold:
                logger.error(
                    "Metric exceeded alert threshold",
                    metric_name=name,
                    agent_id=str(agent_id),
                    value=value,
                    threshold=metric.alert_threshold,
                )

    @with_trace("get_agent_metrics")
    def get_agent_metrics(
        self, agent_id: UUID, metric_name: str | None = None
    ) -> list[MetricSnapshot]:
        """Get metric snapshots for an agent.

        Args:
            agent_id: ID of the agent
            metric_name: Optional name of specific metric to retrieve

        Returns:
            List of metric snapshots
        """
        if agent_id not in self._snapshots:
            return []

        snapshots = self._snapshots[agent_id]
        if metric_name:
            return [s for s in snapshots if metric_name in s.values]
        return snapshots

    @with_trace("get_system_health")
    def get_system_health(self) -> dict[str, float]:
        """Get overall system health metrics.

        Returns:
            Dictionary of health metrics
        """
        total_agents = len(self._snapshots)
        if total_agents == 0:
            return {
                "total_agents": 0,
                "agents_in_error": 0,
                "error_rate": 0.0,
            }

        agents_in_error = sum(
            bool(
                snapshots
                and isinstance(snapshots[-1].metadata.get("agent_state"), str)
                and snapshots[-1].metadata.get("agent_state") == str(AgentState.ERROR)
            )
            for snapshots in self._snapshots.values()
        )

        return {
            "total_agents": total_agents,
            "agents_in_error": agents_in_error,
            "error_rate": agents_in_error / total_agents * 100,
        }

    @with_trace("cleanup_old_snapshots")
    def cleanup_old_snapshots(self, max_age_seconds: int | None = None) -> None:
        """Clean up old metric snapshots.

        Args:
            max_age_seconds: Maximum age of snapshots to keep (defaults to config value)
        """
        if max_age_seconds is None:
            max_age_seconds = self.config.snapshot_retention_seconds

        cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)

        for agent_id in list(self._snapshots.keys()):
            self._snapshots[agent_id] = [
                s for s in self._snapshots[agent_id] if s.timestamp > cutoff
            ]

            if not self._snapshots[agent_id]:
                del self._snapshots[agent_id]

        logger.info("Cleaned up old snapshots", cutoff_time=cutoff)
