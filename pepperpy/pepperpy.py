"""
PepperPy Main Framework Class.

This module provides the main entry point for the PepperPy framework,
coordinating and orchestrating all domain providers.
"""

from typing import Any, Protocol, cast, runtime_checkable

# Import domain providers
from pepperpy.agent.base import AgentProvider, BaseAgentProvider
from pepperpy.cache.base import BaseCacheProvider, CacheProvider
from pepperpy.llm.base import BaseLLMProvider, LLMProvider
from pepperpy.plugin.discovery import PluginDiscoveryProvider
from pepperpy.plugin.registry import plugin_registry
from pepperpy.storage.provider import StorageProvider
from pepperpy.tool.base import BaseToolProvider, ToolProvider
from pepperpy.tts.base import BaseTTSProvider, TTSProvider


# Extended protocol definitions with initialize method
@runtime_checkable
class InitializableProvider(Protocol):
    """Protocol for providers that can be initialized."""

    async def initialize(self) -> None:
        """Initialize the provider."""
        ...


class PepperPy:
    """Main PepperPy framework class that orchestrates all domain providers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the PepperPy framework.

        Args:
            config: Global configuration for all providers
        """
        self.config = config or {}
        self._agent_provider: AgentProvider | None = None
        self._cache_provider: CacheProvider | None = None
        self._discovery_provider: PluginDiscoveryProvider | None = None
        self._llm_provider: LLMProvider | None = None
        self._storage_provider: StorageProvider | None = None
        self._tts_provider: TTSProvider | None = None
        self._tool_provider: ToolProvider | None = None

        # Discover available plugins
        plugin_registry.discover_plugins()

    # Agent provider methods
    def with_agent(
        self, provider: str | type[BaseAgentProvider] | AgentProvider, **config: Any
    ) -> "PepperPy":
        """Configure the agent provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = plugin_registry.get_plugin("agent", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown agent provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("agent", {}), **config}
            self._agent_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(provider, BaseAgentProvider):
            # Create an instance of the provider class
            merged_config = {**self.config.get("agent", {}), **config}
            self._agent_provider = provider(config=merged_config)
        else:
            # Use the provided instance
            self._agent_provider = cast(AgentProvider, provider)

        return self

    # Cache provider methods
    def with_cache(
        self, provider: str | type[BaseCacheProvider] | CacheProvider, **config: Any
    ) -> "PepperPy":
        """Configure the cache provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = plugin_registry.get_plugin("cache", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown cache provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("cache", {}), **config}
            self._cache_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(provider, BaseCacheProvider):
            # Create an instance of the provider class
            merged_config = {**self.config.get("cache", {}), **config}
            self._cache_provider = provider(
                namespace="pepperpy", ttl=3600, config=merged_config
            )
        else:
            # Use the provided instance
            self._cache_provider = cast(CacheProvider, provider)

        return self

    # Discovery provider methods
    def with_discovery(
        self,
        provider: str | type[PluginDiscoveryProvider] | PluginDiscoveryProvider,
        **config: Any,
    ) -> "PepperPy":
        """Configure the discovery provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = plugin_registry.get_plugin("discovery", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown discovery provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("discovery", {}), **config}
            self._discovery_provider = provider_class(merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(
            provider, PluginDiscoveryProvider
        ):
            # Create an instance of the provider class
            merged_config = {**self.config.get("discovery", {}), **config}
            self._discovery_provider = provider(merged_config)
        else:
            # Use the provided instance
            self._discovery_provider = cast(PluginDiscoveryProvider, provider)

        return self

    # Storage provider methods
    def with_storage(
        self,
        provider: Any,
        **config: Any,
    ) -> "PepperPy":
        """Configure the storage provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = plugin_registry.get_plugin("storage", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown storage provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("storage", {}), **config}
            self._storage_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type):
            # Create an instance of the provider class
            merged_config = {**self.config.get("storage", {}), **config}
            self._storage_provider = provider(config=merged_config)  # type: ignore
        else:
            # Use the provided instance
            self._storage_provider = cast(StorageProvider, provider)

        return self

    # TTS provider methods
    def with_tts(
        self, provider: str | type[BaseTTSProvider] | TTSProvider, **config: Any
    ) -> "PepperPy":
        """Configure the TTS provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = plugin_registry.get_plugin("tts", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown TTS provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("tts", {}), **config}
            self._tts_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(provider, BaseTTSProvider):
            # Create an instance of the provider class
            merged_config = {**self.config.get("tts", {}), **config}
            # We use a type ignore here because mypy doesn't recognize that
            # BaseTTSProvider implements TTSProvider
            self._tts_provider = provider(config=merged_config)  # type: ignore
        else:
            # Use the provided instance
            self._tts_provider = cast(TTSProvider, provider)

        return self

    # Tool provider methods
    def with_tool(
        self, provider: str | type[BaseToolProvider] | ToolProvider, **config: Any
    ) -> "PepperPy":
        """Configure the tool provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = plugin_registry.get_plugin("tool", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown tool provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("tool", {}), **config}
            self._tool_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(provider, BaseToolProvider):
            # Create an instance of the provider class
            merged_config = {**self.config.get("tool", {}), **config}
            self._tool_provider = provider(config=merged_config)
        else:
            # Use the provided instance
            self._tool_provider = cast(ToolProvider, provider)

        return self

    # LLM provider methods
    def with_llm(
        self, provider: str | type[BaseLLMProvider] | LLMProvider, **config: Any
    ) -> "PepperPy":
        """Configure the LLM provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = plugin_registry.get_plugin("llm", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown LLM provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("llm", {}), **config}
            self._llm_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(provider, BaseLLMProvider):
            # Create an instance of the provider class
            merged_config = {**self.config.get("llm", {}), **config}
            # We use a type ignore here because mypy doesn't recognize that
            # BaseLLMProvider implements LLMProvider
            self._llm_provider = provider(config=merged_config)  # type: ignore
        else:
            # Use the provided instance
            self._llm_provider = cast(LLMProvider, provider)

        return self

    # Methods to access the domain providers
    @property
    def agent(self) -> AgentProvider:
        """Get the agent provider.

        Returns:
            Agent provider

        Raises:
            ValueError: If no agent provider is configured
        """
        if not self._agent_provider:
            raise ValueError("No agent provider configured. Use with_agent() first.")
        return self._agent_provider

    @property
    def cache(self) -> CacheProvider:
        """Get the cache provider.

        Returns:
            Cache provider

        Raises:
            ValueError: If no cache provider is configured
        """
        if not self._cache_provider:
            raise ValueError("No cache provider configured. Use with_cache() first.")
        return self._cache_provider

    @property
    def discovery(self) -> PluginDiscoveryProvider:
        """Get the discovery provider.

        Returns:
            Discovery provider

        Raises:
            ValueError: If no discovery provider is configured
        """
        if not self._discovery_provider:
            raise ValueError(
                "No discovery provider configured. Use with_discovery() first."
            )
        return self._discovery_provider

    @property
    def storage(self) -> StorageProvider:
        """Get the storage provider.

        Returns:
            Storage provider

        Raises:
            ValueError: If no storage provider is configured
        """
        if not self._storage_provider:
            raise ValueError(
                "No storage provider configured. Use with_storage() first."
            )
        return self._storage_provider

    @property
    def tts(self) -> TTSProvider:
        """Get the TTS provider.

        Returns:
            TTS provider

        Raises:
            ValueError: If no TTS provider is configured
        """
        if not self._tts_provider:
            raise ValueError("No TTS provider configured. Use with_tts() first.")
        return self._tts_provider

    @property
    def tool(self) -> ToolProvider:
        """Get the tool provider.

        Returns:
            Tool provider

        Raises:
            ValueError: If no tool provider is configured
        """
        if not self._tool_provider:
            raise ValueError("No tool provider configured. Use with_tool() first.")
        return self._tool_provider

    @property
    def llm(self) -> LLMProvider:
        """Get the LLM provider.

        Returns:
            LLM provider

        Raises:
            ValueError: If no LLM provider is configured
        """
        if not self._llm_provider:
            raise ValueError("No LLM provider configured. Use with_llm() first.")
        return self._llm_provider

    # Global initialization
    async def initialize(self) -> "PepperPy":
        """Initialize all configured providers.

        Returns:
            Self for method chaining
        """
        # Initialize each provider if configured
        if self._agent_provider and isinstance(
            self._agent_provider, InitializableProvider
        ):
            await self._agent_provider.initialize()

        if self._cache_provider and isinstance(
            self._cache_provider, InitializableProvider
        ):
            await self._cache_provider.initialize()

        if self._discovery_provider and isinstance(
            self._discovery_provider, InitializableProvider
        ):
            await self._discovery_provider.initialize()

        if self._llm_provider and isinstance(self._llm_provider, InitializableProvider):
            await self._llm_provider.initialize()

        if self._storage_provider and isinstance(
            self._storage_provider, InitializableProvider
        ):
            await self._storage_provider.initialize()

        if self._tts_provider and isinstance(self._tts_provider, InitializableProvider):
            await self._tts_provider.initialize()

        if self._tool_provider and isinstance(
            self._tool_provider, InitializableProvider
        ):
            await self._tool_provider.initialize()

        return self
