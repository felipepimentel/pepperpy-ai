#!/usr/bin/env python
"""Example of using PepperPy lifecycle management.

This example demonstrates how to use the lifecycle management components in PepperPy,
including component registration, startup, and shutdown with dependency resolution.
"""

import asyncio
from typing import Any, Dict

from pepperpy.core import initialize
from pepperpy.core.lifecycle import (
    ComponentState,
    create_component_scope,
    get_component,
    has_component,
    register_component,
    shutdown,
    startup,
)
from pepperpy.core.monitoring import get_logger

# Set up logging
initialize(
    environment="development",
    service_name="lifecycle-example",
    log_level="DEBUG",
)

logger = get_logger(__name__)


# Define some component startup/shutdown handlers


async def database_startup() -> Dict[str, Any]:
    """Start the database connection."""
    logger.info("Starting database connection")
    # Simulate connection time
    await asyncio.sleep(0.5)

    # Return a mock database connection
    db = {"connected": True, "name": "example-db"}
    logger.info("Database connected")
    return db


async def database_shutdown(instance: Dict[str, Any]) -> None:
    """Shut down the database connection."""
    logger.info("Closing database connection")
    instance["connected"] = False
    # Simulate disconnection time
    await asyncio.sleep(0.2)
    logger.info("Database disconnected")


async def cache_startup() -> Dict[str, Any]:
    """Start the cache service."""
    logger.info("Starting cache service")
    # Simulate startup time
    await asyncio.sleep(0.3)

    # Return a mock cache service
    cache = {"status": "running", "items": {}}
    logger.info("Cache service started")
    return cache


async def cache_shutdown(instance: Dict[str, Any]) -> None:
    """Shut down the cache service."""
    logger.info("Stopping cache service")
    instance["status"] = "stopped"
    # Simulate shutdown time
    await asyncio.sleep(0.1)
    logger.info("Cache service stopped")


async def api_startup() -> Dict[str, Any]:
    """Start the API server."""
    logger.info("Starting API server")

    # Check dependencies
    if not has_component("database") or not has_component("cache"):
        raise RuntimeError("API server requires database and cache components")

    # Get dependency instances
    db_component = get_component("database")
    cache_component = get_component("cache")

    # Ensure components exist and have instances
    if not db_component or not db_component.instance:
        raise RuntimeError("Database component not started properly")
    if not cache_component or not cache_component.instance:
        raise RuntimeError("Cache component not started properly")

    # Access instances safely now that we've checked they exist
    logger.info(f"API server using database: {db_component.instance['name']}")
    logger.info(f"API server using cache: {cache_component.instance['status']}")

    # Simulate startup time
    await asyncio.sleep(0.4)

    # Return a mock API server
    api = {"status": "running", "port": 8000}
    logger.info("API server started")
    return api


async def api_shutdown(instance: Dict[str, Any]) -> None:
    """Shut down the API server."""
    logger.info("Stopping API server")
    instance["status"] = "stopped"
    # Simulate shutdown time
    await asyncio.sleep(0.2)
    logger.info("API server stopped")


async def background_job_startup() -> Dict[str, Any]:
    """Start the background job processor."""
    logger.info("Starting background job processor")

    # Check dependencies
    if not has_component("database"):
        raise RuntimeError("Background job processor requires database component")

    # Get dependency instance
    db_component = get_component("database")

    # Ensure component exists and has instance
    if not db_component or not db_component.instance:
        raise RuntimeError("Database component not started properly")

    # Access instance safely now that we've checked it exists
    logger.info(
        f"Background job processor using database: {db_component.instance['name']}"
    )

    # Simulate startup time
    await asyncio.sleep(0.3)

    # Return a mock background job processor
    processor = {"status": "running", "jobs": []}
    logger.info("Background job processor started")
    return processor


async def background_job_shutdown(instance: Dict[str, Any]) -> None:
    """Shut down the background job processor."""
    logger.info("Stopping background job processor")
    instance["status"] = "stopped"
    # Simulate shutdown time
    await asyncio.sleep(0.2)
    logger.info("Background job processor stopped")


async def run_example() -> None:
    """Run the lifecycle management example."""
    logger.info("Starting lifecycle management example")

    # Register components with dependencies
    register_component(
        name="database",
        startup=database_startup,
        shutdown=database_shutdown,
        priority=100,  # Highest priority
    )

    register_component(
        name="cache",
        startup=cache_startup,
        shutdown=cache_shutdown,
        priority=90,
    )

    register_component(
        name="api",
        startup=api_startup,
        shutdown=api_shutdown,
        depends_on=["database", "cache"],
        priority=50,
    )

    register_component(
        name="background_jobs",
        startup=background_job_startup,
        shutdown=background_job_shutdown,
        depends_on=["database"],
        priority=40,
    )

    # Start all components
    logger.info("Starting all components")
    await startup()

    # Check component states
    for component_name in ["database", "cache", "api", "background_jobs"]:
        component = get_component(component_name)
        if component:
            logger.info(f"Component {component_name} state: {component.state.value}")

    # Simulate some work
    logger.info("Simulating work...")
    await asyncio.sleep(2)

    # Demonstrate using a component instance
    api_component = get_component("api")
    if api_component and api_component.instance:
        logger.info(f"API server port: {api_component.instance['port']}")

    # Shutdown all components
    logger.info("Shutting down all components")
    await shutdown()

    # Using component scope for temporary components
    logger.info("Demonstrating component scope")

    async with create_component_scope(
        name="temp_component",
        startup=lambda: logger.info("Temporary component started") or {"temp": True},
        shutdown=lambda instance: logger.info("Temporary component stopped"),
    ) as temp_component:
        logger.info(
            f"Temporary component active: {temp_component.state == ComponentState.STARTED}"
        )
        await asyncio.sleep(1)

    logger.info("Lifecycle management example complete")


if __name__ == "__main__":
    # Run the example
    asyncio.run(run_example())
