"""Core metrics module.

This module provides core metrics initialization for monitoring and observability.
"""

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pepperpy.core.metrics.base import Counter, Histogram

from pepperpy.core.metrics import metrics_manager

# Initialize metrics
component_init_counter: Counter | None = None
component_cleanup_counter: Counter | None = None
component_error_counter: Counter | None = None
operation_duration: Histogram | None = None


# Initialize metrics in the background
async def _init_metrics() -> None:
    """Initialize core metrics."""
    global \
        component_init_counter, \
        component_cleanup_counter, \
        component_error_counter, \
        operation_duration

    # Component metrics
    component_init_counter = await metrics_manager.create_counter(
        name="component_init_total",
        description="Total number of component initializations",
    )
    component_cleanup_counter = await metrics_manager.create_counter(
        name="component_cleanup_total",
        description="Total number of component cleanups",
    )
    component_error_counter = await metrics_manager.create_counter(
        name="component_error_total",
        description="Total number of component errors",
    )

    # Operation metrics
    operation_duration = await metrics_manager.create_histogram(
        name="operation_duration_seconds",
        description="Duration of operations in seconds",
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
    )


# Start initialization
asyncio.create_task(_init_metrics())

__all__ = [
    "component_cleanup_counter",
    "component_error_counter",
    "component_init_counter",
    "metrics_manager",
    "operation_duration",
]
