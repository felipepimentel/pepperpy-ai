"""Lazy loading for document processing providers.

This module provides lazy loading for document processing providers
to improve performance by only importing and initializing providers
when they are actually needed.
"""

import importlib
import importlib.util
import inspect
import logging
from typing import Any, Dict, Optional, Type

from .base import DocumentProcessingProvider

logger = logging.getLogger(__name__)


class LazyProviderProxy:
    """Proxy for lazy loading providers.

    This class acts as a proxy for a provider class that will be loaded
    only when it is actually needed.
    """

    def __init__(
        self,
        provider_name: str,
        module_path: str,
        class_name: str,
    ) -> None:
        """Initialize lazy provider proxy.

        Args:
            provider_name: Name of the provider
            module_path: Import path to the provider module
            class_name: Name of the provider class in the module
        """
        self.provider_name = provider_name
        self.module_path = module_path
        self.class_name = class_name
        self._provider_class: Optional[Type[DocumentProcessingProvider]] = None

    def get_provider_class(self) -> Type[DocumentProcessingProvider]:
        """Get the actual provider class (importing it if needed).

        Returns:
            Provider class

        Raises:
            ImportError: If the provider class cannot be imported
            AttributeError: If the provider class does not exist in the module
        """
        if self._provider_class is None:
            try:
                # Import the module
                module = importlib.import_module(self.module_path)

                # Get the provider class from the module
                provider_class = getattr(module, self.class_name)

                # Verify it's a subclass of DocumentProcessingProvider
                if not inspect.isclass(provider_class) or not issubclass(
                    provider_class, DocumentProcessingProvider
                ):
                    raise TypeError(
                        f"Class {self.class_name} in {self.module_path} is not a subclass "
                        f"of DocumentProcessingProvider"
                    )

                self._provider_class = provider_class

            except ImportError as e:
                logger.debug(f"Failed to import provider {self.provider_name}: {e}")
                raise
            except AttributeError as e:
                logger.debug(
                    f"Provider class {self.class_name} not found in {self.module_path}: {e}"
                )
                raise

        return self._provider_class

    def __call__(self, *args: Any, **kwargs: Any) -> DocumentProcessingProvider:
        """Create an instance of the provider.

        Args:
            *args: Positional arguments to pass to the provider constructor
            **kwargs: Keyword arguments to pass to the provider constructor

        Returns:
            Provider instance
        """
        provider_class = self.get_provider_class()
        return provider_class(*args, **kwargs)


# Registry of lazy provider proxies
lazy_provider_registry: Dict[str, LazyProviderProxy] = {}


def register_lazy_provider(
    name: str,
    module_path: str,
    class_name: str,
) -> None:
    """Register a lazy provider proxy.

    Args:
        name: Provider name
        module_path: Import path to the provider module
        class_name: Name of the provider class in the module
    """
    lazy_provider_registry[name.lower()] = LazyProviderProxy(
        provider_name=name,
        module_path=module_path,
        class_name=class_name,
    )


def get_lazy_provider(name: str) -> Optional[LazyProviderProxy]:
    """Get a lazy provider proxy by name.

    Args:
        name: Provider name

    Returns:
        Lazy provider proxy or None if not found
    """
    return lazy_provider_registry.get(name.lower())


def is_module_available(module_name: str) -> bool:
    """Check if a module is available without importing it.

    Args:
        module_name: Name of the module to check

    Returns:
        True if the module is available
    """
    module_spec = importlib.util.find_spec(module_name)
    return module_spec is not None


def register_builtin_providers() -> None:
    """Register built-in providers as lazy providers."""
    # Register PyMuPDF provider
    if is_module_available("fitz"):
        register_lazy_provider(
            name="pymupdf",
            module_path="pepperpy.document_processing.providers.pymupdf_provider",
            class_name="PyMuPDFProvider",
        )

    # Register LangChain provider
    if is_module_available("langchain"):
        register_lazy_provider(
            name="langchain",
            module_path="pepperpy.document_processing.providers.langchain_provider",
            class_name="LangChainProvider",
        )

    # Register Docling provider
    if is_module_available("docling"):
        register_lazy_provider(
            name="docling",
            module_path="pepperpy.document_processing.providers.docling_provider",
            class_name="DoclingProvider",
        )

    # Register LlamaParse provider
    if is_module_available("requests"):
        register_lazy_provider(
            name="llamaparse",
            module_path="pepperpy.document_processing.providers.llamaparse_provider",
            class_name="LlamaParseProvider",
        )


# Initialize the registry
register_builtin_providers()
