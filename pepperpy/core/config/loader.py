"""Dynamic loading system for providers and processors."""

import importlib
from typing import Any, Dict, Type, TypeVar

from .base import ConfigurationError

T = TypeVar("T")


class ProviderLoader:
    """Dynamic loader for providers."""

    @staticmethod
    def load_provider(capability: str, name: str, config: Dict[str, Any]) -> Any:
        """Load and instantiate a provider.

        Args:
            capability: Capability name (e.g. 'llm', 'content')
            name: Provider name within capability
            config: Provider configuration

        Returns:
            Instantiated provider

        Raises:
            ConfigurationError: If provider cannot be loaded or instantiated
        """
        try:
            # Load provider module
            module_path = f"pepperpy.{capability}.providers.{name}"
            module = importlib.import_module(module_path)

            # Get provider class
            provider_class = getattr(module, f"{name.title()}Provider")

            # Instantiate provider
            return provider_class(**config)

        except (ImportError, AttributeError) as e:
            raise ConfigurationError(
                f"Failed to load provider {capability}.{name}: {str(e)}"
            )


class ProcessorLoader:
    """Dynamic loader for processors."""

    @staticmethod
    def load_processor(capability: str, name: str, config: Dict[str, Any]) -> Any:
        """Load and instantiate a processor.

        Args:
            capability: Capability name (e.g. 'content', 'synthesis')
            name: Processor name within capability
            config: Processor configuration

        Returns:
            Instantiated processor

        Raises:
            ConfigurationError: If processor cannot be loaded or instantiated
        """
        try:
            # Load processor module
            module_path = f"pepperpy.{capability}.processors.{name}"
            module = importlib.import_module(module_path)

            # Get processor class
            processor_class = getattr(module, f"{name.title()}Processor")

            # Instantiate processor
            return processor_class(**config)

        except (ImportError, AttributeError) as e:
            raise ConfigurationError(
                f"Failed to load processor {capability}.{name}: {str(e)}"
            )


def load_class(module_path: str, class_name: str, base_class: Type[T]) -> Type[T]:
    """Load a class from a module and validate its type.

    Args:
        module_path: Full path to the module
        class_name: Name of the class to load
        base_class: Base class that loaded class must implement

    Returns:
        Loaded class

    Raises:
        ConfigurationError: If class cannot be loaded or is invalid
    """
    try:
        # Load module
        module = importlib.import_module(module_path)

        # Get class
        loaded_class = getattr(module, class_name)

        # Validate class
        if not issubclass(loaded_class, base_class):
            raise ConfigurationError(
                f"Class {class_name} does not implement {base_class.__name__}"
            )

        return loaded_class

    except (ImportError, AttributeError) as e:
        raise ConfigurationError(
            f"Failed to load class {class_name} from {module_path}: {str(e)}"
        )


__all__ = [
    "ProviderLoader",
    "ProcessorLoader",
    "load_class",
]
