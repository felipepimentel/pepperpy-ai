"""LLM provider management."""

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, ClassVar

from pepperpy.llms.base_llm import BaseLLM, LLMConfig, LLMResponse
from pepperpy.llms.huggingface import HuggingFaceLLM
from pepperpy.llms.openai import OpenAIProvider
from pepperpy.llms.openrouter import OpenRouterProvider


class ProviderStats:
    """Provider usage statistics."""

    def __init__(self) -> None:
        """Initialize provider stats."""
        self.total_requests: int = 0
        self.total_tokens: int = 0
        self.total_cost: float = 0.0
        self.last_used: datetime | None = None
        self.error_count: int = 0


class ProviderConfig:
    """Provider configuration."""

    def __init__(self, provider_type: str, config: dict[str, Any]) -> None:
        """Initialize provider config."""
        self.provider_type = provider_type
        self.config = config
        self.stats = ProviderStats()


class LLMManager:
    """LLM provider manager."""

    # Provider type to class mapping
    PROVIDER_TYPES: ClassVar[dict[str, type[BaseLLM]]] = {
        "openai": OpenAIProvider,
        "openrouter": OpenRouterProvider,
        "huggingface": HuggingFaceLLM,
    }

    def __init__(self) -> None:
        """Initialize LLM manager."""
        self.providers: dict[str, BaseLLM] = {}
        self.provider_configs: dict[str, ProviderConfig] = {}
        self.current_provider: str | None = None

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize LLM providers.

        Args:
            config: Provider configurations

        Raises:
            ValueError: If provider initialization fails
        """
        try:
            # Initialize each provider
            for provider_name, provider_config in config.items():
                provider_type = provider_config.get("type")
                if not provider_type:
                    raise ValueError(f"Provider type not specified for {provider_name}")

                # Get provider class
                provider_class = self._get_provider_class(provider_type)
                if not provider_class:
                    raise ValueError(f"Unknown provider type: {provider_type}")

                # Create and initialize provider
                provider = provider_class(LLMConfig(**provider_config))
                await provider.initialize()

                # Store provider and config
                self.providers[provider_name] = provider
                self.provider_configs[provider_name] = ProviderConfig(
                    provider_type=provider_type, config=provider_config
                )

            # Set default provider
            if self.providers:
                self.current_provider = next(iter(self.providers))

        except Exception as e:
            raise ValueError(f"Failed to initialize providers: {e!s}") from e

    async def generate(
        self, prompt: str, provider: str | None = None, **kwargs: Any
    ) -> LLMResponse:
        """Generate text using specified provider.

        Args:
            prompt: Input prompt
            provider: Optional provider name
            **kwargs: Additional parameters

        Returns:
            Generated response

        Raises:
            ValueError: If generation fails
        """
        provider_name = provider or self.current_provider
        if not provider_name:
            raise ValueError("No provider specified or available")

        provider_instance = self.providers.get(provider_name)
        if not provider_instance:
            raise ValueError(f"Provider not found: {provider_name}")

        try:
            # Generate response
            response = await provider_instance.generate(prompt, **kwargs)

            # Update provider stats
            self._update_stats(
                provider_name, response.tokens_used, response.metadata.get("cost", 0.0)
            )

            return response

        except Exception as e:
            # Update error count
            provider_config = self.provider_configs.get(provider_name)
            if provider_config:
                provider_config.stats.error_count += 1
            raise ValueError(f"Generation failed with {provider_name}: {e!s}") from e

    async def generate_stream(
        self, prompt: str, provider: str | None = None, **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream text using specified provider.

        Args:
            prompt: Input prompt
            provider: Optional provider name
            **kwargs: Additional parameters

        Returns:
            Async iterator of text chunks

        Raises:
            ValueError: If streaming fails
        """
        provider_name = provider or self.current_provider
        if not provider_name:
            raise ValueError("No provider specified or available")

        provider_instance = self.providers.get(provider_name)
        if not provider_instance:
            raise ValueError(f"Provider not found: {provider_name}")

        try:
            # Stream responses
            chunks: list[str] = []
            stream = await provider_instance.generate_stream(prompt, **kwargs)
            async for chunk in stream:
                chunks.append(chunk)
                yield chunk

            # Update provider stats (approximate)
            self._update_stats(
                provider_name,
                len(prompt.split()) + len("".join(chunks).split()),
                0.0,  # Cost tracking not available for streaming
            )

        except Exception as e:
            # Update error count
            provider_config = self.provider_configs.get(provider_name)
            if provider_config:
                provider_config.stats.error_count += 1
            raise ValueError(f"Streaming failed with {provider_name}: {e!s}") from e

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        for provider in self.providers.values():
            await provider.cleanup()
        self.providers.clear()
        self.provider_configs.clear()
        self.current_provider = None

    def _get_provider_class(self, provider_type: str) -> type[BaseLLM] | None:
        """Get provider class by type.

        Args:
            provider_type: Provider type name

        Returns:
            Provider class or None if not found
        """
        return self.PROVIDER_TYPES.get(provider_type)

    def _update_stats(self, provider_name: str, tokens_used: int, cost: float) -> None:
        """Update provider statistics.

        Args:
            provider_name: Provider name
            tokens_used: Number of tokens used
            cost: Cost of request
        """
        provider_config = self.provider_configs.get(provider_name)
        if provider_config:
            provider_config.stats.total_requests += 1
            provider_config.stats.total_tokens += tokens_used
            provider_config.stats.total_cost += cost
            provider_config.stats.last_used = datetime.now()
