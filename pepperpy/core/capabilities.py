"""Provider capability discovery mechanism for PepperPy.

This module provides a capability discovery mechanism for PepperPy providers,
allowing providers to declare their capabilities and clients to discover and
use those capabilities at runtime. This helps ensure that clients only use
capabilities that are supported by the provider they're using.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set


class Capability(Enum):
    """Enumeration of provider capabilities.

    This enumeration defines the capabilities that providers can support.
    Each capability represents a specific feature or functionality that
    a provider may or may not support.
    """

    # LLM capabilities
    TEXT_GENERATION = auto()
    TEXT_EMBEDDING = auto()
    STREAMING = auto()
    FUNCTION_CALLING = auto()
    TOOL_CALLING = auto()
    VISION = auto()
    AUDIO = auto()
    MULTI_MODAL = auto()

    # RAG capabilities
    DOCUMENT_STORAGE = auto()
    DOCUMENT_RETRIEVAL = auto()
    DOCUMENT_SEARCH = auto()
    DOCUMENT_INDEXING = auto()
    DOCUMENT_CHUNKING = auto()
    DOCUMENT_EMBEDDING = auto()
    METADATA_FILTERING = auto()
    HYBRID_SEARCH = auto()
    SEMANTIC_SEARCH = auto()
    KEYWORD_SEARCH = auto()

    # Data capabilities
    KEY_VALUE_STORAGE = auto()
    BATCH_OPERATIONS = auto()
    TTL_SUPPORT = auto()
    METADATA_SUPPORT = auto()
    NAMESPACE_SUPPORT = auto()
    TRANSACTION_SUPPORT = auto()

    # General capabilities
    ASYNC_SUPPORT = auto()
    BATCH_PROCESSING = auto()
    RATE_LIMITING = auto()
    CACHING = auto()
    LOGGING = auto()
    TELEMETRY = auto()
    MONITORING = auto()


class CapabilitySet:
    """Set of capabilities supported by a provider.

    This class represents a set of capabilities that a provider supports.
    It provides methods for checking if a capability is supported and
    for getting the list of supported capabilities.

    Example:
        ```python
        # Create a capability set
        capabilities = CapabilitySet([
            Capability.TEXT_GENERATION,
            Capability.STREAMING,
            Capability.FUNCTION_CALLING,
        ])

        # Check if a capability is supported
        if capabilities.supports(Capability.TEXT_GENERATION):
            # Use text generation
            pass

        # Check if all capabilities are supported
        if capabilities.supports_all([
            Capability.TEXT_GENERATION,
            Capability.STREAMING,
        ]):
            # Use text generation and streaming
            pass

        # Check if any capability is supported
        if capabilities.supports_any([
            Capability.VISION,
            Capability.AUDIO,
        ]):
            # Use vision or audio
            pass
        ```
    """

    def __init__(self, capabilities: Optional[List[Capability]] = None):
        """Initialize the capability set.

        Args:
            capabilities: Optional list of capabilities to include in the set.
        """
        self._capabilities: Set[Capability] = set(capabilities or [])

    def supports(self, capability: Capability) -> bool:
        """Check if a capability is supported.

        Args:
            capability: The capability to check.

        Returns:
            True if the capability is supported, False otherwise.
        """
        return capability in self._capabilities

    def supports_all(self, capabilities: List[Capability]) -> bool:
        """Check if all capabilities are supported.

        Args:
            capabilities: The capabilities to check.

        Returns:
            True if all capabilities are supported, False otherwise.
        """
        return all(self.supports(capability) for capability in capabilities)

    def supports_any(self, capabilities: List[Capability]) -> bool:
        """Check if any capability is supported.

        Args:
            capabilities: The capabilities to check.

        Returns:
            True if any capability is supported, False otherwise.
        """
        return any(self.supports(capability) for capability in capabilities)

    def add(self, capability: Capability) -> None:
        """Add a capability to the set.

        Args:
            capability: The capability to add.
        """
        self._capabilities.add(capability)

    def remove(self, capability: Capability) -> None:
        """Remove a capability from the set.

        Args:
            capability: The capability to remove.
        """
        self._capabilities.discard(capability)

    def clear(self) -> None:
        """Clear all capabilities from the set."""
        self._capabilities.clear()

    def update(self, capabilities: List[Capability]) -> None:
        """Update the set with new capabilities.

        Args:
            capabilities: The capabilities to add to the set.
        """
        self._capabilities.update(capabilities)

    def get_capabilities(self) -> List[Capability]:
        """Get the list of supported capabilities.

        Returns:
            The list of supported capabilities.
        """
        return list(self._capabilities)

    def __contains__(self, capability: Capability) -> bool:
        """Check if a capability is in the set.

        Args:
            capability: The capability to check.

        Returns:
            True if the capability is in the set, False otherwise.
        """
        return capability in self._capabilities

    def __iter__(self):
        """Iterate over the capabilities in the set.

        Returns:
            An iterator over the capabilities in the set.
        """
        return iter(self._capabilities)

    def __len__(self) -> int:
        """Get the number of capabilities in the set.

        Returns:
            The number of capabilities in the set.
        """
        return len(self._capabilities)

    def __str__(self) -> str:
        """Get a string representation of the capability set.

        Returns:
            A string representation of the capability set.
        """
        return f"CapabilitySet({[c.name for c in self._capabilities]})"

    def __repr__(self) -> str:
        """Get a string representation of the capability set.

        Returns:
            A string representation of the capability set.
        """
        return self.__str__()


class CapabilityRegistry:
    """Registry for provider capabilities.

    This class provides a registry for provider capabilities, allowing
    providers to register their capabilities and clients to discover
    those capabilities at runtime.

    Example:
        ```python
        # Register provider capabilities
        CapabilityRegistry.register_provider(
            "openai",
            CapabilitySet([
                Capability.TEXT_GENERATION,
                Capability.STREAMING,
                Capability.FUNCTION_CALLING,
            ])
        )

        # Get provider capabilities
        capabilities = CapabilityRegistry.get_provider_capabilities("openai")

        # Check if a provider supports a capability
        if CapabilityRegistry.provider_supports("openai", Capability.TEXT_GENERATION):
            # Use text generation with OpenAI
            pass
        ```
    """

    _registry: Dict[str, CapabilitySet] = {}

    @classmethod
    def register_provider(cls, provider_id: str, capabilities: CapabilitySet) -> None:
        """Register a provider's capabilities.

        Args:
            provider_id: The ID of the provider.
            capabilities: The capabilities supported by the provider.
        """
        cls._registry[provider_id] = capabilities

    @classmethod
    def get_provider_capabilities(cls, provider_id: str) -> CapabilitySet:
        """Get a provider's capabilities.

        Args:
            provider_id: The ID of the provider.

        Returns:
            The capabilities supported by the provider.

        Raises:
            KeyError: If the provider is not registered.
        """
        if provider_id not in cls._registry:
            raise KeyError(f"Provider '{provider_id}' is not registered")
        return cls._registry[provider_id]

    @classmethod
    def provider_supports(cls, provider_id: str, capability: Capability) -> bool:
        """Check if a provider supports a capability.

        Args:
            provider_id: The ID of the provider.
            capability: The capability to check.

        Returns:
            True if the provider supports the capability, False otherwise.
        """
        try:
            return cls.get_provider_capabilities(provider_id).supports(capability)
        except KeyError:
            return False

    @classmethod
    def provider_supports_all(
        cls, provider_id: str, capabilities: List[Capability]
    ) -> bool:
        """Check if a provider supports all capabilities.

        Args:
            provider_id: The ID of the provider.
            capabilities: The capabilities to check.

        Returns:
            True if the provider supports all capabilities, False otherwise.
        """
        try:
            return cls.get_provider_capabilities(provider_id).supports_all(capabilities)
        except KeyError:
            return False

    @classmethod
    def provider_supports_any(
        cls, provider_id: str, capabilities: List[Capability]
    ) -> bool:
        """Check if a provider supports any capability.

        Args:
            provider_id: The ID of the provider.
            capabilities: The capabilities to check.

        Returns:
            True if the provider supports any capability, False otherwise.
        """
        try:
            return cls.get_provider_capabilities(provider_id).supports_any(capabilities)
        except KeyError:
            return False

    @classmethod
    def get_providers_with_capability(cls, capability: Capability) -> List[str]:
        """Get all providers that support a capability.

        Args:
            capability: The capability to check.

        Returns:
            A list of provider IDs that support the capability.
        """
        return [
            provider_id
            for provider_id, capabilities in cls._registry.items()
            if capabilities.supports(capability)
        ]

    @classmethod
    def get_providers_with_all_capabilities(
        cls, capabilities: List[Capability]
    ) -> List[str]:
        """Get all providers that support all capabilities.

        Args:
            capabilities: The capabilities to check.

        Returns:
            A list of provider IDs that support all capabilities.
        """
        return [
            provider_id
            for provider_id, provider_capabilities in cls._registry.items()
            if provider_capabilities.supports_all(capabilities)
        ]

    @classmethod
    def get_providers_with_any_capability(
        cls, capabilities: List[Capability]
    ) -> List[str]:
        """Get all providers that support any capability.

        Args:
            capabilities: The capabilities to check.

        Returns:
            A list of provider IDs that support any capability.
        """
        return [
            provider_id
            for provider_id, provider_capabilities in cls._registry.items()
            if provider_capabilities.supports_any(capabilities)
        ]

    @classmethod
    def clear(cls) -> None:
        """Clear the registry."""
        cls._registry.clear()


# Convenience functions


def register_provider_capabilities(
    provider_id: str, capabilities: List[Capability]
) -> None:
    """Register a provider's capabilities.

    Args:
        provider_id: The ID of the provider.
        capabilities: The capabilities supported by the provider.
    """
    CapabilityRegistry.register_provider(provider_id, CapabilitySet(capabilities))


def get_provider_capabilities(provider_id: str) -> List[Capability]:
    """Get a provider's capabilities.

    Args:
        provider_id: The ID of the provider.

    Returns:
        The capabilities supported by the provider.

    Raises:
        KeyError: If the provider is not registered.
    """
    return CapabilityRegistry.get_provider_capabilities(provider_id).get_capabilities()


def provider_supports(provider_id: str, capability: Capability) -> bool:
    """Check if a provider supports a capability.

    Args:
        provider_id: The ID of the provider.
        capability: The capability to check.

    Returns:
        True if the provider supports the capability, False otherwise.
    """
    return CapabilityRegistry.provider_supports(provider_id, capability)


def get_providers_with_capability(capability: Capability) -> List[str]:
    """Get all providers that support a capability.

    Args:
        capability: The capability to check.

    Returns:
        A list of provider IDs that support the capability.
    """
    return CapabilityRegistry.get_providers_with_capability(capability)


def require_capability(provider_id: str, capability: Capability) -> None:
    """Require that a provider supports a capability.

    Args:
        provider_id: The ID of the provider.
        capability: The capability to require.

    Raises:
        ValueError: If the provider does not support the capability.
    """
    if not provider_supports(provider_id, capability):
        raise ValueError(
            f"Provider '{provider_id}' does not support capability '{capability.name}'"
        )


def require_capabilities(provider_id: str, capabilities: List[Capability]) -> None:
    """Require that a provider supports all capabilities.

    Args:
        provider_id: The ID of the provider.
        capabilities: The capabilities to require.

    Raises:
        ValueError: If the provider does not support all capabilities.
    """
    missing = [c for c in capabilities if not provider_supports(provider_id, c)]
    if missing:
        missing_names = [c.name for c in missing]
        raise ValueError(
            f"Provider '{provider_id}' does not support capabilities: {missing_names}"
        )
