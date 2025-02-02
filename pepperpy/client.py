"""Main client interface for Pepperpy.

This module provides a simple, high-level interface for using Pepperpy,
with automatic configuration and provider management.
"""

from collections.abc import AsyncGenerator

from pepperpy.config.auto import AutoConfig
from pepperpy.providers.manager import ProviderManager
from pepperpy.providers.services.openrouter import OpenRouterProvider


class PepperpyClient:
    """Main client interface for Pepperpy.

    This class provides a simple way to use Pepperpy with minimal configuration.
    It automatically handles provider setup, fallback, and resource management.

    Example:
        ```python
        from pepperpy import PepperpyClient

        # Create client (uses environment variables)
        client = PepperpyClient()

        # Simple completion
        response = await client.complete("Hello, how are you?")
        print(response)

        # Streaming completion
        async for chunk in client.chat_stream("Tell me a story"):
            print(chunk, end="")
        ```
    """

    def __init__(
        self,
        config: AutoConfig | None = None,
        load_dotenv: bool = True,
    ) -> None:
        """Initialize the Pepperpy client.

        Args:
            config: Optional explicit configuration
            load_dotenv: Whether to load .env file
        """
        self.config = config or AutoConfig.from_env(load_dotenv_file=load_dotenv)
        self._manager: ProviderManager | None = None

    async def initialize(self) -> None:
        """Initialize the client and providers.

        This is called automatically when needed, but can be called
        explicitly to pre-initialize resources.
        """
        if self._manager is not None:
            return

        # Create primary provider
        primary_config = self.config.get_provider_config(is_fallback=False)
        primary_provider = OpenRouterProvider(primary_config)

        # Create fallback provider if configured
        fallback_provider = None
        try:
            fallback_config = self.config.get_provider_config(is_fallback=True)
            fallback_provider = OpenRouterProvider(fallback_config)
        except ValueError:
            pass

        # Create and initialize manager
        self._manager = ProviderManager(primary_provider, fallback_provider)
        await self._manager.initialize()

    async def cleanup(self) -> None:
        """Cleanup resources.

        This should be called when done with the client to properly
        clean up resources.
        """
        if self._manager:
            await self._manager.cleanup()
            self._manager = None

    async def __aenter__(self) -> "PepperpyClient":
        """Enter async context manager."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.cleanup()

    async def _ensure_initialized(self) -> None:
        """Ensure client is initialized."""
        if not self._manager:
            await self.initialize()

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
    ) -> str:
        """Complete a prompt.

        Args:
            prompt: The prompt to complete
            temperature: Sampling temperature

        Returns:
            The completed text
        """
        await self._ensure_initialized()
        return await self._manager.complete(
            prompt=prompt,
            temperature=temperature,
            stream=False,
        )

    async def chat_stream(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion.

        Args:
            prompt: The prompt to complete
            temperature: Sampling temperature

        Yields:
            Text chunks as they are generated
        """
        await self._ensure_initialized()
        response = await self._manager.complete(
            prompt=prompt,
            temperature=temperature,
            stream=True,
        )
        if isinstance(response, AsyncGenerator):
            async for chunk in response:
                yield chunk
        else:
            yield response  # Fallback for non-streaming response
