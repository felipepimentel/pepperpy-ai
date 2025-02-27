"""Registry for RAG components."""

from typing import Dict, List, Optional, Type, TypeVar

from .base import (
    Augmenter,
    Chunker,
    Embedder,
    Indexer,
    RagComponent,
    Retriever,
)

T = TypeVar("T", bound=RagComponent)


class ComponentRegistry:
    """Registry for managing RAG components."""

    def __init__(self):
        """Initialize empty component registry."""
        self._components: Dict[str, Dict[str, Type[RagComponent]]] = {
            "chunker": {},
            "embedder": {},
            "indexer": {},
            "retriever": {},
            "augmenter": {},
        }

    def register(self, component_type: str, name: str, component_class: Type[T]):
        """Register a component class.

        Args:
            component_type: Type of component (chunker, embedder, etc.)
            name: Name to register the component under
            component_class: Component class to register
        """
        if component_type not in self._components:
            raise ValueError(f"Unknown component type: {component_type}")

        self._components[component_type][name] = component_class

    def get(self, component_type: str, name: str) -> Type[RagComponent]:
        """Get a registered component class.

        Args:
            component_type: Type of component to get
            name: Name of the component

        Returns:
            Registered component class

        Raises:
            KeyError: If component not found
        """
        if component_type not in self._components:
            raise ValueError(f"Unknown component type: {component_type}")

        if name not in self._components[component_type]:
            raise KeyError(f"No {component_type} registered with name: {name}")

        return self._components[component_type][name]

    def list_components(
        self, component_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """List registered components.

        Args:
            component_type: Optional type to filter by

        Returns:
            Dictionary mapping component types to lists of registered names
        """
        if component_type:
            if component_type not in self._components:
                raise ValueError(f"Unknown component type: {component_type}")
            return {component_type: list(self._components[component_type].keys())}

        return {
            ctype: list(components.keys())
            for ctype, components in self._components.items()
        }

    def register_chunker(self, name: str, chunker_class: Type[Chunker]):
        """Register a chunker implementation."""
        self.register("chunker", name, chunker_class)

    def register_embedder(self, name: str, embedder_class: Type[Embedder]):
        """Register an embedder implementation."""
        self.register("embedder", name, embedder_class)

    def register_indexer(self, name: str, indexer_class: Type[Indexer]):
        """Register an indexer implementation."""
        self.register("indexer", name, indexer_class)

    def register_retriever(self, name: str, retriever_class: Type[Retriever]):
        """Register a retriever implementation."""
        self.register("retriever", name, retriever_class)

    def register_augmenter(self, name: str, augmenter_class: Type[Augmenter]):
        """Register an augmenter implementation."""
        self.register("augmenter", name, augmenter_class)

    def get_chunker(self, name: str) -> Type[Chunker]:
        """Get a registered chunker class."""
        return self.get("chunker", name)  # type: ignore

    def get_embedder(self, name: str) -> Type[Embedder]:
        """Get a registered embedder class."""
        return self.get("embedder", name)  # type: ignore

    def get_indexer(self, name: str) -> Type[Indexer]:
        """Get a registered indexer class."""
        return self.get("indexer", name)  # type: ignore

    def get_retriever(self, name: str) -> Type[Retriever]:
        """Get a registered retriever class."""
        return self.get("retriever", name)  # type: ignore

    def get_augmenter(self, name: str) -> Type[Augmenter]:
        """Get a registered augmenter class."""
        return self.get("augmenter", name)  # type: ignore


# Global registry instance
registry = ComponentRegistry()
