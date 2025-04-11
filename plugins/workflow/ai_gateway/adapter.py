"""Direct adapter for AI Gateway functionality."""

import asyncio
import logging
from typing import Any, cast

from pepperpy.core.base import PepperpyError
from pepperpy.core.types import ComponentType

from .gateway import GatewayRequest
from .run_mesh import MockModelProvider, create_mock_provider


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
        self.provider: MockModelProvider | None = None
        self.initialized = False

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
            provider = await create_mock_provider()
            self.provider = cast(MockModelProvider, provider)
            await self.provider.initialize()
            self.initialized = True
            self.logger.debug("Initialized AI Gateway adapter")
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


async def run_direct() -> None:
    """Run adapter directly for testing."""
    async with AIGatewayAdapter() as adapter:
        result = await adapter.execute({
            "operation": "chat",
            "messages": [{"role": "user", "content": "Test message"}],
        })
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(run_direct())
