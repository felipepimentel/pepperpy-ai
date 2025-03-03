"""Registry for RAG components.

This module provides a registry for RAG components, allowing them to be
registered and retrieved by ID.
"""

from typing import Dict, Optional, TypeVar

from pepperpy.core.logging import get_logger
from pepperpy.rag.base import RagComponent
from pepperpy.rag.generation import Generator
from pepperpy.rag.indexing import DocumentIndexer
from pepperpy.rag.retrieval import Retriever
from pepperpy.rag.types import RagComponentType

logger = get_logger(__name__)

T = TypeVar("T", bound=RagComponent)


class RagRegistry:
    """Registry for RAG components."""

    def __init__(self):
        """Initialize the registry."""
        self._components: Dict[str, RagComponent] = {}
        self._component_types: Dict[RagComponentType, Dict[str, RagComponent]] = {
            component_type: {} for component_type in RagComponentType
        }

    def register(self, component: RagComponent) -> None:
        """Register a component.

        Args:
            component: The component to register

        Raises:
            ValueError: If a component with the same ID is already registered

        """
        if component.component_id in self._components:
            raise ValueError(
                f"Component already registered with ID: {component.component_id}",
            )

        self._components[component.component_id] = component
        self._component_types[component.component_type][
            component.component_id
        ] = component

        logger.debug(
            f"Registered {component.component_type.name} component: {component.name} "
            f"(ID: {component.component_id})",
        )

    def get(self, component_id: str) -> Optional[RagComponent]:
        """Get a component by ID.

        Args:
            component_id: The ID of the component to get

        Returns:
            The component if found, None otherwise

        """
        return self._components.get(component_id)

    def get_by_type(
        self, component_type: RagComponentType, component_id: str,
    ) -> Optional[RagComponent]:
        """Get a component by type and ID.

        Args:
            component_type: The type of the component
            component_id: The ID of the component

        Returns:
            The component if found, None otherwise

        """
        return self._component_types[component_type].get(component_id)

    def get_all(self) -> Dict[str, RagComponent]:
        """Get all registered components.

        Returns:
            A dictionary of component IDs to components

        """
        return self._components.copy()

    def get_all_by_type(
        self, component_type: RagComponentType,
    ) -> Dict[str, RagComponent]:
        """Get all components of a specific type.

        Args:
            component_type: The type of components to get

        Returns:
            A dictionary of component IDs to components

        """
        return self._component_types[component_type].copy()

    def get_indexer(self, component_id: str) -> Optional[DocumentIndexer]:
        """Get an indexer by ID.

        Args:
            component_id: The ID of the indexer to get

        Returns:
            The indexer if found, None otherwise

        """
        component = self.get_by_type(RagComponentType.DOCUMENT_INDEXER, component_id)
        if component is None:
            return None
        return component  # type: ignore

    def get_retriever(self, component_id: str) -> Optional[Retriever]:
        """Get a retriever by ID.

        Args:
            component_id: The ID of the retriever to get

        Returns:
            The retriever if found, None otherwise

        """
        component = self.get_by_type(RagComponentType.RETRIEVER, component_id)
        if component is None:
            return None
        return component  # type: ignore

    def get_generator(self, component_id: str) -> Optional[Generator]:
        """Get a generator by ID.

        Args:
            component_id: The ID of the generator to get

        Returns:
            The generator if found, None otherwise

        """
        component = self.get_by_type(RagComponentType.GENERATOR, component_id)
        if component is None:
            return None
        return component  # type: ignore

    async def initialize_all(self) -> None:
        """Initialize all registered components."""
        logger.info("Initializing all registered RAG components")
        for component in self._components.values():
            await component.initialize()

    async def cleanup_all(self) -> None:
        """Clean up all registered components."""
        logger.info("Cleaning up all registered RAG components")
        for component in self._components.values():
            await component.cleanup()


# Global registry instance
rag_registry = RagRegistry()
