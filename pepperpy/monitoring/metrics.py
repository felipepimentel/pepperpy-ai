"""Metrics system for tracking workflow performance.

This module provides functionality to track and analyze workflow execution metrics,
helping to identify performance bottlenecks and optimize workflows.
"""

import time
from collections.abc import Callable
from datetime import datetime, timedelta
from types import TracebackType
from typing import Any, Dict, List, Optional, Union

import structlog
from pydantic import BaseModel

from pepperpy.core.enums import MetricType

__all__ = ["Metrics", "metrics"]

# Type aliases for better readability
MetricValue = Union[int, float]
MetricLabels = dict[str, str]
MetricCallback = Callable[[], MetricValue]

log = structlog.get_logger("pepperpy.monitoring.metrics")


class StepMetrics(BaseModel):
    """Metrics for a workflow step execution."""

    step_name: str
    agent_name: str
    action: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    token_usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class WorkflowMetrics(BaseModel):
    """Metrics for a complete workflow execution."""

    workflow_name: str
    workflow_version: str
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    total_token_usage: Optional[Dict[str, int]] = None
    steps: List[StepMetrics] = []
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class MetricsTracker:
    """Tracker for workflow execution metrics."""

    def __init__(self):
        """Initialize the metrics tracker."""
        self._current_workflow: Optional[WorkflowMetrics] = None
        self._current_step: Optional[StepMetrics] = None

    async def start_workflow(
        self,
        workflow_name: str,
        workflow_version: str,
        execution_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Start tracking a workflow execution.

        Args:
        ----
            workflow_name: Name of the workflow
            workflow_version: Version of the workflow
            execution_id: Unique ID for this execution
            metadata: Optional metadata about the execution

        """
        self._current_workflow = WorkflowMetrics(
            workflow_name=workflow_name,
            workflow_version=workflow_version,
            execution_id=execution_id,
            start_time=datetime.now(),
            metadata=metadata or {},
        )

    async def end_workflow(self, error: Optional[str] = None) -> WorkflowMetrics:
        """End tracking the current workflow execution.

        Args:
        ----
            error: Optional error message if workflow failed

        Returns:
        -------
            Complete workflow metrics

        Raises:
        ------
            ValueError: If no workflow is being tracked

        """
        if not self._current_workflow:
            raise ValueError("No workflow is being tracked")

        self._current_workflow.end_time = datetime.now()
        self._current_workflow.duration_ms = (
            self._current_workflow.end_time - self._current_workflow.start_time
        ).total_seconds() * 1000

        if error:
            self._current_workflow.error = error

        # Calculate total token usage
        total_usage: Dict[str, int] = {}
        for step in self._current_workflow.steps:
            if step.token_usage:
                for key, value in step.token_usage.items():
                    total_usage[key] = total_usage.get(key, 0) + value
        self._current_workflow.total_token_usage = total_usage

        metrics = self._current_workflow
        self._current_workflow = None
        return metrics

    async def start_step(
        self,
        step_name: str,
        agent_name: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Start tracking a workflow step execution.

        Args:
        ----
            step_name: Name of the step
            agent_name: Name of the agent executing the step
            action: Action being performed
            metadata: Optional metadata about the step

        Raises:
        ------
            ValueError: If no workflow is being tracked

        """
        if not self._current_workflow:
            raise ValueError("No workflow is being tracked")

        self._current_step = StepMetrics(
            step_name=step_name,
            agent_name=agent_name,
            action=action,
            start_time=datetime.now(),
            metadata=metadata or {},
        )

    async def end_step(
        self,
        token_usage: Optional[Dict[str, int]] = None,
        error: Optional[str] = None,
    ) -> None:
        """End tracking the current step execution.

        Args:
        ----
            token_usage: Optional token usage statistics
            error: Optional error message if step failed

        Raises:
        ------
            ValueError: If no step is being tracked

        """
        if not self._current_workflow or not self._current_step:
            raise ValueError("No step is being tracked")

        self._current_step.end_time = datetime.now()
        self._current_step.duration_ms = (
            self._current_step.end_time - self._current_step.start_time
        ).total_seconds() * 1000

        if token_usage:
            self._current_step.token_usage = token_usage
        if error:
            self._current_step.error = error

        self._current_workflow.steps.append(self._current_step)
        self._current_step = None

    async def add_workflow_metadata(self, metadata: Dict[str, Any]) -> None:
        """Add metadata to the current workflow.

        Args:
        ----
            metadata: Metadata to add

        Raises:
        ------
            ValueError: If no workflow is being tracked

        """
        if not self._current_workflow:
            raise ValueError("No workflow is being tracked")

        self._current_workflow.metadata.update(metadata)

    async def add_step_metadata(self, metadata: Dict[str, Any]) -> None:
        """Add metadata to the current step.

        Args:
        ----
            metadata: Metadata to add

        Raises:
        ------
            ValueError: If no step is being tracked

        """
        if not self._current_step:
            raise ValueError("No step is being tracked")

        self._current_step.metadata.update(metadata)


class MetricsContext:
    """Context manager for tracking workflow and step metrics."""

    def __init__(
        self,
        tracker: MetricsTracker,
        workflow_name: Optional[str] = None,
        workflow_version: Optional[str] = None,
        execution_id: Optional[str] = None,
        step_name: Optional[str] = None,
        agent_name: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the metrics context.

        Args:
        ----
            tracker: MetricsTracker instance
            workflow_name: Optional name of the workflow
            workflow_version: Optional version of the workflow
            execution_id: Optional execution ID
            step_name: Optional name of the step
            agent_name: Optional name of the agent
            action: Optional action being performed
            metadata: Optional metadata

        """
        self.tracker = tracker
        self.workflow_name = workflow_name
        self.workflow_version = workflow_version
        self.execution_id = execution_id
        self.step_name = step_name
        self.agent_name = agent_name
        self.action = action
        self.metadata = metadata
        self._error: Optional[str] = None
        self._token_usage: Optional[Dict[str, int]] = None

    async def __aenter__(self) -> "MetricsContext":
        """Enter the context and start tracking metrics.

        Returns
        -------
            Self for method chaining

        """
        if self.workflow_name:
            await self.tracker.start_workflow(
                self.workflow_name,
                self.workflow_version or "unknown",
                self.execution_id or str(time.time_ns()),
                self.metadata,
            )

        if self.step_name:
            await self.tracker.start_step(
                self.step_name,
                self.agent_name or "unknown",
                self.action or "unknown",
                self.metadata,
            )

        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Exit the context and finish tracking metrics.

        Args:
        ----
            exc_type: The type of the exception that was raised
            exc_val: The instance of the exception that was raised
            exc_tb: The traceback of the exception that was raised

        """
        error = str(exc_val) if exc_val else None

        if self.step_name:
            await self.tracker.end_step(self._token_usage, error)

        if self.workflow_name:
            await self.tracker.end_workflow(error)

    async def set_token_usage(self, usage: Dict[str, int]) -> None:
        """Set token usage for the current step.

        Args:
        ----
            usage: Token usage statistics

        """
        self._token_usage = usage


class Metrics:
    """Metrics collector for monitoring system behavior."""

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._metrics: dict[str, tuple[MetricType, MetricValue]] = {}
        self._callbacks: dict[str, tuple[MetricType, MetricCallback]] = {}

    async def register_callback(
        self,
        name: str,
        callback: MetricCallback,
        metric_type: MetricType,
    ) -> None:
        """Register a callback for collecting metrics.

        Args:
        ----
            name: Metric name
            callback: Function that returns the metric value
            metric_type: Type of metric to collect

        """
        self._callbacks[name] = (metric_type, callback)

    async def record_metric(
        self,
        name: str,
        value: MetricValue,
        metric_type: MetricType,
        labels: MetricLabels | None = None,
    ) -> None:
        """Record a metric value.

        Args:
        ----
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Optional metric labels

        """
        self._metrics[name] = (metric_type, value)

    async def get_metric(self, name: str) -> tuple[MetricType, MetricValue] | None:
        """Get a metric value.

        Args:
        ----
            name: Metric name

        Returns:
        -------
            Tuple of metric type and value, or None if not found

        """
        if name in self._metrics:
            return self._metrics[name]
        if name in self._callbacks:
            metric_type, callback = self._callbacks[name]
            value = callback()
            return metric_type, value
        return None

    async def clear_metric(self, name: str) -> None:
        """Clear a metric.

        Args:
        ----
            name: Metric name

        """
        self._metrics.pop(name, None)
        self._callbacks.pop(name, None)

    async def clear_all(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()
        self._callbacks.clear()


# Create default metrics instance
metrics = Metrics()


def parse_time_period(period: str) -> timedelta:
    """Parse a time period string into a timedelta.

    Args:
    ----
        period: Time period string (e.g., "24h", "7d", "30d")

    Returns:
    -------
        Equivalent timedelta

    Raises:
    ------
        ValueError: If period format is invalid

    """
    unit = period[-1].lower()
    try:
        value = int(period[:-1])
    except ValueError:
        raise ValueError(f"Invalid period format: {period}")

    if unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    elif unit == "w":
        return timedelta(weeks=value)
    else:
        raise ValueError(f"Invalid time unit: {unit}")


async def get_search_stats(
    index_name: Optional[str] = None, period: str = "24h"
) -> Dict[str, Any]:
    """Get search usage statistics.

    Args:
    ----
        index_name: Optional index to filter stats for
        period: Time period to get stats for (e.g., "24h", "7d", "30d")

    Returns:
    -------
        Dict containing search statistics

    """
    try:
        time_period = parse_time_period(period)
        start_time = datetime.now() - time_period

        # TODO: Implement actual metrics collection
        stats = {
            "queries": {"total": 1000, "avg_latency": 50.5, "cache_hit_rate": 85.5},
            "indexing": {
                "docs_indexed": 5000,
                "index_size": 1024 * 1024 * 10,
                "avg_index_time": 25.5,
            },
            "errors": {"query_errors": 10, "index_errors": 5, "validation_errors": 2},
        }

        log.info(
            "Retrieved search stats",
            extra={
                "index": index_name,
                "period": period,
                "start_time": start_time.isoformat(),
            },
        )

        return stats

    except Exception as e:
        log.error(
            "Failed to get search stats",
            extra={"error": str(e), "index": index_name, "period": period},
        )
        raise
