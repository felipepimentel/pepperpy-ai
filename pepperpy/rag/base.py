"""Base classes for the RAG system.

This module provides the base classes and interfaces for the RAG system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar

from pepperpy.core.logging import get_logger
from pepperpy.rag.types import RagComponentType, RagResponse, SearchQuery

logger = get_logger(__name__)

T = TypeVar("T", bound="RagComponent")


class RagComponent(ABC):
    """Base class for all RAG components."""

    component_type: RagComponentType = RagComponentType.CUSTOM

    def __init__(self, component_id: str, name: str, description: str = ""):
        """Initialize the RAG component.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name for the component
            description: Description of the component's functionality
        """
        self.component_id = component_id
        self.name = name
        self.description = description
        self.initialized = False
        self.config: Dict[str, Any] = {}

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        This method should be called before using the component.
        """
        self.initialized = True
        logger.info(f"Initialized RAG component: {self.name}")

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources used by the component.

        This method should be called when the component is no longer needed.
        """
        self.initialized = False
        logger.info(f"Cleaned up RAG component: {self.name}")

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the component with the provided configuration.

        Args:
            config: Configuration dictionary
        """
        self.config.update(config)
        logger.debug(f"Updated configuration for component: {self.name}")

    @classmethod
    def create(cls: Type[T], component_id: str, name: str, **kwargs) -> T:
        """Create a new instance of the component.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name for the component
            **kwargs: Additional arguments to pass to the constructor

        Returns:
            A new instance of the component
        """
        return cls(component_id, name, **kwargs)


class RagPipeline(RagComponent):
    """Base class for RAG pipelines.

    A RAG pipeline orchestrates the flow of data through indexing,
    retrieval, and generation components.
    """

    component_type = RagComponentType.PIPELINE

    def __init__(self, component_id: str, name: str, description: str = ""):
        """Initialize the RAG pipeline.

        Args:
            component_id: Unique identifier for the pipeline
            name: Human-readable name for the pipeline
            description: Description of the pipeline's functionality
        """
        super().__init__(component_id, name, description)
        self.components: Dict[str, RagComponent] = {}

    def add_component(self, component: RagComponent) -> None:
        """Add a component to the pipeline.

        Args:
            component: The component to add
        """
        self.components[component.component_id] = component
        logger.debug(f"Added component {component.name} to pipeline {self.name}")

    def get_component(self, component_id: str) -> Optional[RagComponent]:
        """Get a component by ID.

        Args:
            component_id: The ID of the component to get

        Returns:
            The component if found, None otherwise
        """
        return self.components.get(component_id)

    @abstractmethod
    async def process(self, query: SearchQuery) -> RagResponse:
        """Process a query through the pipeline.

        Args:
            query: The query to process

        Returns:
            The generated response
        """
        pass

    async def initialize(self) -> None:
        """Initialize all components in the pipeline."""
        logger.info(f"Initializing RAG pipeline: {self.name}")
        for component in self.components.values():
            await component.initialize()
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up all components in the pipeline."""
        logger.info(f"Cleaning up RAG pipeline: {self.name}")
        for component in self.components.values():
            await component.cleanup()
        await super().cleanup()
