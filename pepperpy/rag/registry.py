"""Registry for managing RAG components."""

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
    """Registry for RAG components."""

    def __init__(self):
        self._components: Dict[str, Dict[str, Type[RagComponent]]] = {
            "chunker": {},
            "embedder": {},
            "indexer": {},
            "retriever": {},
            "augmenter": {},
        }

    def register(self, component_type: str, name: str, component_class: Type[T]):
        """Register a component class."""
        if component_type not in self._components:
            raise ValueError(f"Invalid component type: {component_type}")

        if name in self._components[component_type]:
            raise ValueError(
                f"Component {name} already registered for type {component_type}"
            )

        self._components[component_type][name] = component_class

    def get(self, component_type: str, name: str) -> Type[RagComponent]:
        """Get a registered component class."""
        if component_type not in self._components:
            raise ValueError(f"Invalid component type: {component_type}")

        if name not in self._components[component_type]:
            raise ValueError(f"Component {name} not found for type {component_type}")

        return self._components[component_type][name]

    def list_components(
        self, component_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """List registered components."""
        if component_type:
            if component_type not in self._components:
                raise ValueError(f"Invalid component type: {component_type}")
            return {component_type: list(self._components[component_type].keys())}

        return {
            ctype: list(components.keys())
            for ctype, components in self._components.items()
        }

    def register_chunker(self, name: str, chunker_class: Type[Chunker]):
        """Register a chunker component."""
        self.register("chunker", name, chunker_class)

    def register_embedder(self, name: str, embedder_class: Type[Embedder]):
        """Register an embedder component."""
        self.register("embedder", name, embedder_class)

    def register_indexer(self, name: str, indexer_class: Type[Indexer]):
        """Register an indexer component."""
        self.register("indexer", name, indexer_class)

    def register_retriever(self, name: str, retriever_class: Type[Retriever]):
        """Register a retriever component."""
        self.register("retriever", name, retriever_class)

    def register_augmenter(self, name: str, augmenter_class: Type[Augmenter]):
        """Register an augmenter component."""
        self.register("augmenter", name, augmenter_class)


# Global component registry
registry = ComponentRegistry()
