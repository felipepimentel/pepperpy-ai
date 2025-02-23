"""Example Name: Simple Agent
Description: Example showing how to create and use a basic agent
Category: basic
Dependencies: pepperpy
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from examples.utils import ExampleComponent, example

# Configure logging
logger = logging.getLogger(__name__)


class SimpleAgent(ExampleComponent):
    """Simple agent implementation."""

    async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data.

        Args:
            data: Data to process

        Returns:
            Dict[str, Any]: Processed data
        """
        self._operations.inc()
        try:
            # Simulate work
            await asyncio.sleep(0.1)

            # Process data
            result = {
                "input": data,
                "processed": True,
                "timestamp": datetime.now().isoformat(),
            }

            self._duration.observe(0.1)
            return result

        except Exception:
            self._errors.inc()
            raise

    async def _execute(self) -> None:
        """Execute agent operation."""
        self._operations.inc()
        try:
            # Process test data
            data = {"message": "Hello, Agent!"}
            result = await self.process_data(data)
            logger.info(f"Processed data: {result}")
            self._duration.observe(0.1)

        except Exception:
            self._errors.inc()
            raise


@example(
    name="Simple Agent",
    category="basic",
    description="Example showing how to create and use a basic agent",
)
async def main() -> Dict[str, Any]:
    """Run simple agent example.

    Returns:
        Dict[str, Any]: Example output
    """
    # Create agent
    agent = SimpleAgent("simple_agent")

    try:
        # Initialize agent
        await agent._initialize()

        # Process data
        data = {"message": "Hello, Agent!"}
        result = await agent.process_data(data)

        # Get metrics
        operations = agent._operations.get_value()
        duration = agent._duration.get_value()["count"]
        logger.info(f"Executed {operations} operations in {duration:.2f} seconds")

        return result

    finally:
        # Clean up agent
        await agent._cleanup()


if __name__ == "__main__":
    # Run example
    asyncio.run(main())
