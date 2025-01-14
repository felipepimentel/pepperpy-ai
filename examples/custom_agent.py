"""Example of custom agent implementation."""

from typing import Any, cast

from pepperpy_core import Message, Provider

from pepperpy.agents.base import BaseAgent
from pepperpy.agents.factory import AgentFactory


class CustomReviewAgent(BaseAgent):
    """Custom code review agent implementation."""

    async def _setup(self) -> None:
        """Setup agent resources."""
        # Initialize capabilities
        for capability in self.config.capabilities:
            if capability == "code_review":
                # Initialize code review capability
                pass
            elif capability == "security_audit":
                # Initialize security audit capability
                pass

    async def _teardown(self) -> None:
        """Cleanup agent resources."""
        # Cleanup capabilities
        pass

    async def execute(self, task: str, **kwargs: Any) -> Message:
        """Execute agent task.

        Args:
            task: Task description.
            **kwargs: Additional task parameters.

        Returns:
            Message: Agent response message.
        """
        if not self._provider:
            raise ValueError("Provider not configured")
        return await self._provider.generate(task)


async def main() -> None:
    """Example usage of custom agent."""
    # Create factory
    factory = AgentFactory()

    # Register custom agent type
    factory.register("custom-reviewer", CustomReviewAgent)

    # Create agent from YAML
    agent = factory.from_yaml("review/code_reviewer.yml")

    # Configure provider
    provider = cast(Provider, Provider.anthropic())
    agent.use(provider)

    # Initialize agent
    await agent.initialize()

    # Execute task
    result = await agent.execute(
        "Review this code for security vulnerabilities",
        context="def process_data(data): return eval(data)",
    )
    print(result)

    # Cleanup
    await agent.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
