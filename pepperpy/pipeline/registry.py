"""Registry for pipeline providers."""

from typing import Dict, List, Type, TypeVar

from pepperpy.pipeline.base import Pipeline

T = TypeVar("T")  # Input type
U = TypeVar("U")  # Output type

# Registry of pipeline providers
_PIPELINE_REGISTRY: Dict[str, Type[Pipeline]] = {}


def register_pipeline(name: str, pipeline_class: Type[Pipeline]) -> None:
    """Register a pipeline provider class.

    Args:
        name: Name of the pipeline provider
        pipeline_class: Pipeline provider class

    """
    _PIPELINE_REGISTRY[name] = pipeline_class


def get_pipeline_class(name: str) -> Type[Pipeline]:
    """Get a pipeline provider class by name.

    Args:
        name: Name of the pipeline provider

    Returns:
        Type[Pipeline]: Pipeline provider class

    Raises:
        ValueError: If pipeline provider is not found

    """
    if name not in _PIPELINE_REGISTRY:
        raise ValueError(f"Pipeline provider '{name}' not found in registry")
    return _PIPELINE_REGISTRY[name]


def list_pipelines() -> List[str]:
    """List all registered pipeline providers.

    Returns:
        List[str]: List of pipeline provider names

    """
    return list(_PIPELINE_REGISTRY.keys())


def get_pipeline_registry() -> Dict[str, Type[Pipeline]]:
    """Get the pipeline provider registry.

    Returns:
        Dict[str, Type[Pipeline]]: Copy of the pipeline provider registry

    """
    return _PIPELINE_REGISTRY.copy()
