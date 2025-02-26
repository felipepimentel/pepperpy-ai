"""Unified provider for managing multiple providers."""

from .base import Provider, ProviderConfig, ProviderError


class UnifiedProvider:
    """Unified provider for managing multiple providers."""

    def __init__(self):
        """Initialize unified provider."""
        self._providers: dict[str, Provider] = {}
        self._provider_types: dict[str, type[Provider]] = {}

    def register_provider(self, provider_type: type[Provider], name: str) -> None:
        """Register provider type.

        Args:
            provider_type: Provider class to register
            name: Provider name

        Raises:
            ProviderError: If provider with same name already registered
        """
        if name in self._provider_types:
            raise ProviderError(f"Provider {name} already registered")
        self._provider_types[name] = provider_type

    def get_provider(self, name: str) -> Provider | None:
        """Get provider by name.

        Args:
            name: Provider name

        Returns:
            Optional[Provider]: Provider if found, None otherwise
        """
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """List all registered providers.

        Returns:
            List[str]: List of provider names
        """
        return list(self._provider_types.keys())

    async def initialize_provider(self, name: str, config: ProviderConfig) -> Provider:
        """Initialize provider with configuration.

        Args:
            name: Provider name
            config: Provider configuration

        Returns:
            Provider: Initialized provider

        Raises:
            ProviderError: If provider not registered or initialization fails
        """
        if name not in self._provider_types:
            raise ProviderError(f"Provider {name} not registered")

        provider_type = self._provider_types[name]
        provider = provider_type(config)
        await provider.initialize()
        self._providers[name] = provider
        return provider

    async def shutdown_provider(self, name: str) -> None:
        """Shutdown provider.

        Args:
            name: Provider name

        Raises:
            ProviderError: If provider not found
        """
        provider = self._providers.get(name)
        if not provider:
            raise ProviderError(f"Provider {name} not found")

        await provider.shutdown()
        del self._providers[name]

    async def shutdown_all(self) -> None:
        """Shutdown all providers."""
        for name in list(self._providers.keys()):
            await self.shutdown_provider(name)
