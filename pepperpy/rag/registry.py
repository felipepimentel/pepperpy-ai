"""Registry for RAG components."""

from typing import Dict, List, Optional, Type, TypeVar

from pepperpy.core.logging import get_logger
from pepperpy.core.registry import (
    ComponentMetadata,
    Registry,
    get_registry,
)

from .base import (
    Augmenter,
    Chunker,
    Embedder,
    Indexer,
    RagComponent,
    Retriever,
)

logger = get_logger(__name__)
T = TypeVar("T", bound=RagComponent)


class ComponentRegistry(Registry[RagComponent]):
    """Registry for managing RAG components."""

    def __init__(self):
        """Initialize empty component registry."""
        super().__init__(RagComponent)
        self._component_categories = {
            "chunker": Chunker,
            "embedder": Embedder,
            "indexer": Indexer,
            "retriever": Retriever,
            "augmenter": Augmenter,
        }

    def register(self, component_type: str, name: str, component_class: Type[T]):
        """Register a component class.

        Args:
            component_type: Type of component (chunker, embedder, etc.)
            name: Name to register the component under
            component_class: Component class to register
        """
        if component_type not in self._component_categories:
            raise ValueError(f"Unknown component type: {component_type}")

        expected_base = self._component_categories[component_type]
        if not issubclass(component_class, expected_base):
            raise TypeError(f"Component must be a subclass of {expected_base.__name__}")

        metadata = ComponentMetadata(
            name=name,
            description=component_class.__doc__ or "",
            tags={component_type},
            properties={"category": component_type},
        )

        try:
            self.register_type(f"{component_type}.{name}", component_class, metadata)
        except Exception as e:
            logger.error(f"Failed to register {component_type} '{name}': {e}")
            raise

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
        if component_type not in self._component_categories:
            raise ValueError(f"Unknown component type: {component_type}")

        try:
            return self.get_type(f"{component_type}.{name}")
        except Exception as e:
            raise KeyError(f"No {component_type} registered with name: {name}") from e

    def list_components(
        self, component_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """List registered components.

        Args:
            component_type: Optional type to filter by

        Returns:
            Dictionary mapping component types to lists of registered names
        """
        result = {}
        types = self.list_component_types()

        for full_name in types:
            if "." not in full_name:
                continue

            cat, name = full_name.split(".", 1)

            if component_type and cat != component_type:
                continue

            if cat not in result:
                result[cat] = []

            result[cat].append(name)

        return result

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
_registry = None


def get_component_registry() -> ComponentRegistry:
    """Get the global RAG component registry instance."""
    global _registry
    if _registry is None:
        _registry = ComponentRegistry()
        # Register with the global registry manager
        try:
            registry_manager = get_registry()
            registry_manager.register_registry("rag", _registry)
        except Exception as e:
            logger.warning(f"Failed to register with global registry: {e}")
    return _registry


# For backwards compatibility
registry = get_component_registry()
