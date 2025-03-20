#!/usr/bin/env python
"""Example of using PepperPy monitoring components.

This example demonstrates how to use the monitoring components in PepperPy,
including metrics, tracing, logging, and health checks.
"""

import asyncio
import random
from typing import List

from pepperpy.core import initialize
from pepperpy.core.monitoring import (
    HealthCheck,
    HealthStatus,
    Timer,
    Tracer,
    configure_logging,
    get_logger,
    monitor,
    register_health_check,
)

# Set up logger
configure_logging(level="DEBUG")
logger = get_logger(__name__)


# Create a custom health check
class RandomHealthCheck(HealthCheck):
    """Health check that randomly returns healthy or degraded."""

    def __init__(self):
        super().__init__("random")

    async def _perform_check(self):
        """Perform the health check."""
        # Simulate a check that sometimes returns degraded
        if random.random() < 0.3:
            return HealthStatus.DEGRADED, {"reason": "Random degradation"}
        return HealthStatus.HEALTHY, {"message": "All good"}


# Decorate a function with monitoring
@monitor(metric_tags={"type": "example"})
async def process_items(items: List[str]) -> int:
    """Process a list of items with monitoring.

    Args:
        items: Items to process

    Returns:
        Number of processed items
    """
    logger.info(f"Processing {len(items)} items")

    # Create a processing span
    with Tracer("processing", tags={"item_count": len(items)}):
        processed = 0

        # Process each item
        for item in items:
            await process_item(item)
            processed += 1

        logger.info(f"Processed {processed} items")
        return processed


async def process_item(item: str) -> None:
    """Process a single item.

    Args:
        item: Item to process
    """
    # Time the processing
    with Timer("item_processing", tags={"item": item}):
        # Simulate processing time
        delay = random.uniform(0.1, 0.5)
        logger.debug(f"Processing item {item} (delay: {delay:.2f}s)")
        await asyncio.sleep(delay)


async def run_example():
    """Run the monitoring example."""
    # Initialize the framework with monitoring
    initialize(
        environment="development",
        service_name="example",
        log_level="DEBUG",
        metrics_enabled=True,
        tracing_enabled=True,
        health_checks_enabled=True,
    )

    # Register health check
    register_health_check(RandomHealthCheck())

    # Generate some test data
    items = [f"item_{i}" for i in range(10)]

    # Process in batches
    logger.info("Starting example run")

    for batch_num in range(3):
        batch = random.sample(items, 5)  # Random batch of 5 items
        logger.info(f"Processing batch {batch_num + 1}")

        # Process the batch
        with Tracer(f"batch_{batch_num}", tags={"batch_size": len(batch)}):
            count = await process_items(batch)
            logger.info(f"Batch {batch_num + 1} complete: {count} items processed")

    # Check health
    from pepperpy.core.monitoring import check_health, get_health_status

    health_results = await check_health()
    overall_status = get_health_status()

    logger.info(f"Health check results: {health_results}")
    logger.info(f"Overall health status: {overall_status}")

    # Print metrics
    from pepperpy.core.monitoring.metrics import MetricsRegistry

    metrics = MetricsRegistry.get_metrics()
    logger.info(f"Collected {len(metrics)} metrics")

    for i, metric in enumerate(metrics[:5]):  # Show first 5 metrics
        logger.info(f"Metric {i + 1}: {metric.name} = {metric.value} {metric.tags}")

    logger.info("Example complete")


if __name__ == "__main__":
    # Run the example
    asyncio.run(run_example())
