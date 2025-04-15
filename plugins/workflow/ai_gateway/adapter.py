"""Direct adapter for AI Gateway functionality."""

import asyncio
import logging
import os
from typing import Any

from pepperpy.core.base import PepperpyError
from pepperpy.core.types import ComponentType

from .gateway import GatewayRequest, ModelProvider


class AIGatewayAdapter:
    """Direct adapter for AI Gateway functionality.

    Use this adapter for development, testing or when bypassing the plugin system.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize adapter.

        Args:
            **kwargs: Configuration parameters
        """
        self.config = kwargs
        self.logger = logging.getLogger(__name__)
        self.provider: ModelProvider | None = None
        self.initialized = False

        # Configuration
        self.provider_type = kwargs.get(
            "provider_type", os.environ.get("PEPPERPY_LLM_PROVIDER", "openai")
        )
        self.model_id = kwargs.get(
            "model_id", os.environ.get("PEPPERPY_LLM_MODEL", "gpt-3.5-turbo")
        )

    async def __aenter__(self) -> "AIGatewayAdapter":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, *_: Any) -> None:
        """Async context manager exit."""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize adapter resources.

        Raises:
            PepperpyError: If initialization fails
        """
        if self.initialized:
            return

        try:
            self.provider = await self._get_provider()
            if self.provider:
                await self.provider.initialize()
            self.initialized = True
            self.logger.debug(
                f"Initialized AI Gateway adapter with provider {self.provider_type}"
            )
        except Exception as e:
            self.provider = None
            self.initialized = False
            raise PepperpyError(f"Failed to initialize adapter: {e}") from e

    async def cleanup(self) -> None:
        """Clean up adapter resources."""
        if not self.initialized:
            return

        try:
            if self.provider:
                await self.provider.cleanup()
            self.initialized = False
            self.logger.debug("Cleaned up AI Gateway adapter")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute adapter functionality.

        Args:
            input_data: Input parameters including operation

        Returns:
            Execution results

        Raises:
            PepperpyError: If execution fails
        """
        if not self.initialized:
            await self.initialize()

        try:
            request = GatewayRequest(
                request_id=input_data.get("request_id", "direct-1"),
                operation=input_data.get("operation", "chat"),
                inputs=input_data,
                target=ComponentType.MODEL,
            )

            if not self.provider:
                raise PepperpyError("Provider not initialized")

            response = await self.provider.execute(request)
            return response.to_dict()

        except Exception as e:
            raise PepperpyError(f"Execution failed: {e}") from e

    async def _get_provider(self) -> ModelProvider | None:
        """Get provider based on configuration.

        Returns:
            Model provider instance
        """
        # Import gateway module for provider creation
        from .gateway import create_model_provider

        try:
            # Use real provider based on configuration
            return await create_model_provider(
                provider_type=self.provider_type, model_id=self.model_id, **self.config
            )
        except ImportError as e:
            self.logger.error(f"Failed to import provider {self.provider_type}: {e}")
            raise PepperpyError(f"Provider {self.provider_type} not available") from e


async def run_direct() -> None:
    """Run adapter directly for testing."""
    # Use environment variables or default to a real provider
    provider_type = os.environ.get("PEPPERPY_LLM_PROVIDER", "openai")
    model_id = os.environ.get("PEPPERPY_LLM_MODEL", "gpt-3.5-turbo")

    async with AIGatewayAdapter(
        provider_type=provider_type, model_id=model_id
    ) as adapter:
        result = await adapter.execute(
            {
                "operation": "chat",
                "messages": [{"role": "user", "content": "Test message"}],
            }
        )
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(run_direct())
