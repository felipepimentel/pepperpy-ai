"""Component metadata system for PepperPy.

This module provides a metadata system for components, allowing them to
self-describe and be discovered by the Hub.
"""

import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union, cast

from .base.common import BaseComponent

# Special attribute name for storing metadata
METADATA_ATTR = "_component_metadata_"


class ComponentCategory(Enum):
    """Categories for components."""

    AUDIO = "audio"
    CACHING = "caching"
    FORMATS = "formats"
    IMAGE = "image"
    MEMORY = "memory"
    MULTIMODAL = "multimodal"
    OBSERVABILITY = "observability"
    PROVIDERS = "providers"
    RAG = "rag"
    SYNTHESIS = "synthesis"
    TEXT = "text"
    VECTOR = "vector"
    WORKFLOW = "workflow"
    OTHER = "other"


@dataclass
class ComponentMetadata:
    """Metadata for a component."""

    name: str
    description: str
    category: ComponentCategory
    input: List[str] = field(default_factory=list)
    output: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    version: str = "0.1.0"
    author: str = ""
    homepage: str = ""
    license: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary.

        Returns:
            Dictionary representation of metadata

        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "input": self.input,
            "output": self.output,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "tags": list(self.tags),
            "version": self.version,
            "author": self.author,
            "homepage": self.homepage,
            "license": self.license,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComponentMetadata":
        """Create metadata from dictionary.

        Args:
            data: Dictionary representation of metadata

        Returns:
            Component metadata

        """
        category = data.get("category", "other")
        if isinstance(category, str):
            try:
                category = ComponentCategory(category)
            except ValueError:
                category = ComponentCategory.OTHER

        tags = data.get("tags", [])
        if isinstance(tags, list):
            tags = set(tags)
        else:
            tags = set()

        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=category,
            input=data.get("input", []),
            output=data.get("output", []),
            parameters=data.get("parameters", {}),
            dependencies=data.get("dependencies", []),
            tags=tags,
            version=data.get("version", "0.1.0"),
            author=data.get("author", ""),
            homepage=data.get("homepage", ""),
            license=data.get("license", ""),
            extra=data.get("extra", {}),
        )


T = TypeVar("T", bound=Type[BaseComponent])


# Define the method outside the decorator to avoid linter issues
def _get_component_metadata(self: Any) -> ComponentMetadata:
    """Get component metadata.

    Returns:
        Component metadata

    """
    return getattr(self.__class__, METADATA_ATTR)


def component(
    name: str,
    description: str,
    category: Union[ComponentCategory, str],
    input: Optional[List[str]] = None,
    output: Optional[List[str]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    dependencies: Optional[List[str]] = None,
    tags: Optional[Union[List[str], Set[str]]] = None,
    version: str = "0.1.0",
    author: str = "",
    homepage: str = "",
    license: str = "",
    **extra: Any,
) -> Callable[[T], T]:
    """Decorator for adding metadata to a component.

    Args:
        name: Component name
        description: Component description
        category: Component category
        input: Input types
        output: Output types
        parameters: Parameter descriptions
        dependencies: Component dependencies
        tags: Component tags
        version: Component version
        author: Component author
        homepage: Component homepage
        license: Component license
        **extra: Additional metadata

    Returns:
        Decorated component class

    """

    def decorator(cls: T) -> T:
        if not issubclass(cls, BaseComponent):
            raise TypeError(f"Class {cls.__name__} must inherit from BaseComponent")

        # Convert category to enum if it's a string
        cat: ComponentCategory
        if isinstance(category, str):
            try:
                cat = ComponentCategory(category)
            except ValueError:
                cat = ComponentCategory.OTHER
        else:
            cat = category

        # Convert tags to set
        tag_set = set()
        if tags:
            tag_set = set(tags)

        # Create metadata
        metadata = ComponentMetadata(
            name=name,
            description=description,
            category=cat,
            input=input or [],
            output=output or [],
            parameters=parameters or {},
            dependencies=dependencies or [],
            tags=tag_set,
            version=version,
            author=author,
            homepage=homepage,
            license=license,
            extra=extra,
        )

        # Add metadata to class using setattr
        setattr(cls, METADATA_ATTR, metadata)

        # Add method to class dictionary directly
        # This is a workaround for type checking issues
        cls_dict = dict(cls.__dict__)
        cls_dict["get_component_metadata"] = _get_component_metadata

        # Create a new class with the same name and bases but updated dict
        updated_cls = type(cls.__name__, cls.__bases__, cls_dict)

        # Copy all attributes from original class to new class
        for attr_name, attr_value in cls.__dict__.items():
            if attr_name not in updated_cls.__dict__ and not attr_name.startswith("__"):
                setattr(updated_cls, attr_name, attr_value)

        return cast(T, updated_cls)

    return decorator


def get_metadata(component_class: Type[BaseComponent]) -> Optional[ComponentMetadata]:
    """Get metadata from a component class.

    Args:
        component_class: Component class

    Returns:
        Component metadata or None if not found

    """
    return getattr(component_class, METADATA_ATTR, None)


class ComponentRegistry:
    """Registry for components with metadata."""

    def __init__(self) -> None:
        """Initialize component registry."""
        self._components: Dict[str, Type[BaseComponent]] = {}
        self._categories: Dict[ComponentCategory, List[str]] = {
            category: [] for category in ComponentCategory
        }
        self._tags: Dict[str, List[str]] = {}

    def register(self, component_class: Type[BaseComponent]) -> None:
        """Register a component.

        Args:
            component_class: Component class to register

        Raises:
            ValueError: If component doesn't have metadata

        """
        metadata = get_metadata(component_class)
        if metadata is None:
            raise ValueError(
                f"Component {component_class.__name__} doesn't have metadata",
            )

        self._components[metadata.name] = component_class

        # Add to category index
        self._categories[metadata.category].append(metadata.name)

        # Add to tag index
        for tag in metadata.tags:
            if tag not in self._tags:
                self._tags[tag] = []
            self._tags[tag].append(metadata.name)

    def get_component(self, name: str) -> Optional[Type[BaseComponent]]:
        """Get component by name.

        Args:
            name: Component name

        Returns:
            Component class or None if not found

        """
        return self._components.get(name)

    def get_components_by_category(
        self, category: ComponentCategory,
    ) -> List[Type[BaseComponent]]:
        """Get components by category.

        Args:
            category: Component category

        Returns:
            List of component classes

        """
        return [self._components[name] for name in self._categories.get(category, [])]

    def get_components_by_tag(self, tag: str) -> List[Type[BaseComponent]]:
        """Get components by tag.

        Args:
            tag: Component tag

        Returns:
            List of component classes

        """
        return [self._components[name] for name in self._tags.get(tag, [])]

    def get_all_components(self) -> List[Type[BaseComponent]]:
        """Get all registered components.

        Returns:
            List of all component classes

        """
        return list(self._components.values())

    def get_metadata(self, name: str) -> Optional[ComponentMetadata]:
        """Get metadata for a component.

        Args:
            name: Component name

        Returns:
            Component metadata or None if not found

        """
        component_class = self._components.get(name)
        if not component_class:
            return None

        return get_metadata(component_class)

    def get_all_metadata(self) -> Dict[str, ComponentMetadata]:
        """Get metadata for all components.

        Returns:
            Dictionary mapping component names to metadata

        """
        result: Dict[str, ComponentMetadata] = {}
        for name, component_class in self._components.items():
            metadata = get_metadata(component_class)
            if metadata is not None:
                result[name] = metadata
        return result


# Global component registry
registry = ComponentRegistry()


def register_component(component_class: Type[BaseComponent]) -> Type[BaseComponent]:
    """Register a component with the global registry.

    Args:
        component_class: Component class to register

    Returns:
        The component class (for chaining)

    """
    registry.register(component_class)
    return component_class


def get_component(name: str) -> Optional[Type[BaseComponent]]:
    """Get a component from the global registry.

    Args:
        name: Component name

    Returns:
        Component class or None if not found

    """
    return registry.get_component(name)


def get_components_by_category(
    category: ComponentCategory,
) -> List[Type[BaseComponent]]:
    """Get components by category from the global registry.

    Args:
        category: Component category

    Returns:
        List of component classes

    """
    return registry.get_components_by_category(category)


def get_components_by_tag(tag: str) -> List[Type[BaseComponent]]:
    """Get components by tag from the global registry.

    Args:
        tag: Component tag

    Returns:
        List of component classes

    """
    return registry.get_components_by_tag(tag)


def discover_components(module: Any) -> List[Type[BaseComponent]]:
    """Discover components in a module.

    Args:
        module: Module to search for components

    Returns:
        List of discovered component classes

    """
    components = []
    for _name, obj in inspect.getmembers(module):
        if (
            inspect.isclass(obj)
            and issubclass(obj, BaseComponent)
            and hasattr(obj, METADATA_ATTR)
        ):
            components.append(obj)
            registry.register(obj)
    return components
