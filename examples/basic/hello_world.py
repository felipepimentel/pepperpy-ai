"""Example Name: Hello World
Description: Simple example showing basic framework setup and usage
Category: basic
Dependencies: pepperpy
"""

import asyncio
import logging

from examples.utils import ExampleComponent, example

# Configure logging
logger = logging.getLogger(__name__)


class HelloComponent(ExampleComponent):
    """Hello world component implementation."""

    async def _execute(self) -> None:
        """Execute component operation."""
        self._operations.inc()
        try:
            # Simulate work
            await asyncio.sleep(0.1)
            logger.info("Hello, World!")
            self._duration.observe(0.1)
        except Exception:
            self._errors.inc()
            raise


@example(
    name="Hello World",
    category="basic",
    description="Simple example showing basic framework setup and usage",
)
async def main() -> str:
    """Run hello world example.

    Returns:
        str: Example output
    """
    # Create component
    component = HelloComponent("hello")

    try:
        # Initialize component
        await component._initialize()

        # Execute component
        await component._execute()

        # Get metrics
        operations = component._operations.get_value()
        duration = component._duration.get_value()["count"]
        logger.info(f"Executed {operations} operations in {duration:.2f} seconds")

        return "Hello, World!"

    finally:
        # Clean up component
        await component._cleanup()


if __name__ == "__main__":
    # Run example
    asyncio.run(main())
