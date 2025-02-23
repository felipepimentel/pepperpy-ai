"""Example Name: Custom Provider
Description: Example showing how to create and use a custom provider
Category: intermediate
Dependencies: pepperpy
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from examples.utils import ExampleComponent, example

# Configure logging
logger = logging.getLogger(__name__)


class DataProvider(ExampleComponent):
    """Custom data provider implementation."""

    def __init__(self, name: str) -> None:
        """Initialize provider.

        Args:
            name: Provider name
        """
        super().__init__(name)
        self._data: Dict[str, Any] = {}

    async def store_data(self, key: str, value: Any) -> None:
        """Store data.

        Args:
            key: Data key
            value: Data value
        """
        self._operations.inc()
        try:
            # Simulate work
            await asyncio.sleep(0.1)

            # Store data with timestamp
            self._data[key] = {
                "value": value,
                "timestamp": datetime.now().isoformat(),
            }

            self._duration.observe(0.1)
            logger.info(f"Stored data: {key}={value}")

        except Exception:
            self._errors.inc()
            raise

    async def get_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data.

        Args:
            key: Data key

        Returns:
            Optional[Dict[str, Any]]: Data value and metadata
        """
        self._operations.inc()
        try:
            # Simulate work
            await asyncio.sleep(0.1)

            # Get data
            data = self._data.get(key)

            self._duration.observe(0.1)
            if data:
                logger.info(f"Retrieved data: {key}={data}")
            else:
                logger.warning(f"Data not found: {key}")

            return data

        except Exception:
            self._errors.inc()
            raise

    async def _execute(self) -> None:
        """Execute provider operation."""
        self._operations.inc()
        try:
            # Store test data
            await self.store_data("test", "Hello, Provider!")

            # Get test data
            data = await self.get_data("test")
            logger.info(f"Test data: {data}")

            self._duration.observe(0.1)

        except Exception:
            self._errors.inc()
            raise


class DataConsumer(ExampleComponent):
    """Data consumer implementation."""

    async def process_data(
        self, provider: DataProvider, key: str
    ) -> Optional[Dict[str, Any]]:
        """Process data from provider.

        Args:
            provider: Data provider
            key: Data key

        Returns:
            Optional[Dict[str, Any]]: Processed data
        """
        self._operations.inc()
        try:
            # Get data from provider
            data = await provider.get_data(key)
            if not data:
                return None

            # Process data
            result = {
                "key": key,
                "data": data,
                "processed": True,
                "timestamp": datetime.now().isoformat(),
            }

            self._duration.observe(0.1)
            return result

        except Exception:
            self._errors.inc()
            raise

    async def _execute(self) -> None:
        """Execute consumer operation."""
        self._operations.inc()
        try:
            # Create provider
            provider = DataProvider("test_provider")
            await provider._initialize()

            try:
                # Store test data
                await provider.store_data("test", "Hello, Consumer!")

                # Process test data
                result = await self.process_data(provider, "test")
                logger.info(f"Processed data: {result}")

                self._duration.observe(0.1)

            finally:
                # Clean up provider
                await provider._cleanup()

        except Exception:
            self._errors.inc()
            raise


@example(
    name="Custom Provider",
    category="intermediate",
    description="Example showing how to create and use a custom provider",
)
async def main() -> Dict[str, Any]:
    """Run custom provider example.

    Returns:
        Dict[str, Any]: Example output
    """
    # Create provider and consumer
    provider = DataProvider("data_provider")
    consumer = DataConsumer("data_consumer")

    try:
        # Initialize components
        await provider._initialize()
        await consumer._initialize()

        # Store data
        await provider.store_data("example", "Hello, World!")

        # Process data
        result = await consumer.process_data(provider, "example")

        # Get metrics
        provider_ops = provider._operations.get_value()
        consumer_ops = consumer._operations.get_value()
        total_duration = (
            provider._duration.get_value()["count"]
            + consumer._duration.get_value()["count"]
        )
        logger.info(
            f"Executed {provider_ops + consumer_ops} operations "
            f"in {total_duration:.2f} seconds"
        )

        return result or {}

    finally:
        # Clean up components
        await consumer._cleanup()
        await provider._cleanup()


if __name__ == "__main__":
    # Run example
    asyncio.run(main())
