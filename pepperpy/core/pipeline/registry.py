"""Pipeline registry module.

This module provides a registry for storing and retrieving pipelines.
It ensures that pipelines can be registered, unregistered, and retrieved
by name in a thread-safe manner.

Example:
    >>> from pepperpy.core.pipeline import Pipeline, PipelineRegistry
    >>> registry = PipelineRegistry()
    >>> pipeline = Pipeline("example")
    >>> registry.register(pipeline)
    >>> assert registry.get("example") == pipeline
"""

import logging
from typing import Dict, List

from pepperpy.core.pipeline.base import Pipeline

logger = logging.getLogger(__name__)


class PipelineRegistry:
    """Registry for storing and retrieving pipelines.

    This class provides a central registry for pipelines, allowing them to be
    stored and retrieved by name. It is implemented as a singleton to ensure
    there is only one registry instance.

    Example:
        >>> registry = PipelineRegistry()
        >>> pipeline = Pipeline("example")
        >>> registry.register(pipeline)
        >>> assert registry.get("example") == pipeline
    """

    _instance = None
    _pipelines: Dict[str, Pipeline] = {}

    def __new__(cls) -> "PipelineRegistry":
        """Create a new instance or return the existing one.

        Returns:
            The singleton registry instance
        """
        if cls._instance is None:
            cls._instance = super(PipelineRegistry, cls).__new__(cls)
        return cls._instance

    def register(self, pipeline: Pipeline) -> None:
        """Register a pipeline.

        Args:
            pipeline: The pipeline to register

        Raises:
            ValueError: If a pipeline with the same name already exists

        Example:
            >>> registry = PipelineRegistry()
            >>> pipeline = Pipeline("example")
            >>> registry.register(pipeline)
        """
        if pipeline.name in self._pipelines:
            raise ValueError(f"Pipeline with name '{pipeline.name}' already registered")

        self._pipelines[pipeline.name] = pipeline
        logger.debug(f"Registered pipeline: {pipeline.name}")

    def unregister(self, name: str) -> None:
        """Unregister a pipeline.

        Args:
            name: The name of the pipeline to unregister

        Raises:
            KeyError: If no pipeline with the given name exists

        Example:
            >>> registry = PipelineRegistry()
            >>> pipeline = Pipeline("example")
            >>> registry.register(pipeline)
            >>> registry.unregister("example")
        """
        if name not in self._pipelines:
            raise KeyError(f"No pipeline registered with name '{name}'")

        del self._pipelines[name]
        logger.debug(f"Unregistered pipeline: {name}")

    def get(self, name: str) -> Pipeline:
        """Get a pipeline by name.

        Args:
            name: The name of the pipeline to get

        Returns:
            The pipeline with the given name

        Raises:
            KeyError: If no pipeline with the given name exists

        Example:
            >>> registry = PipelineRegistry()
            >>> pipeline = Pipeline("example")
            >>> registry.register(pipeline)
            >>> assert registry.get("example") == pipeline
        """
        if name not in self._pipelines:
            raise KeyError(f"No pipeline registered with name '{name}'")

        return self._pipelines[name]

    def list(self) -> List[str]:
        """List all registered pipeline names.

        Returns:
            A sorted list of registered pipeline names

        Example:
            >>> registry = PipelineRegistry()
            >>> pipeline = Pipeline("example")
            >>> registry.register(pipeline)
            >>> assert "example" in registry.list()
        """
        return sorted(self._pipelines.keys())

    def clear(self) -> None:
        """Clear all registered pipelines.

        Example:
            >>> registry = PipelineRegistry()
            >>> pipeline = Pipeline("example")
            >>> registry.register(pipeline)
            >>> registry.clear()
            >>> assert len(registry.list()) == 0
        """
        self._pipelines.clear()
        logger.debug("Cleared all registered pipelines")
