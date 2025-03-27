"""Example demonstrating a minimal PepperPy setup without external services.

This example shows a simple usage pattern that doesn't require any external APIs
or services, making it easier to run for demonstration purposes.
"""

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import pepperpy
from pepperpy.llm.base import GenerationChunk, GenerationResult, Message, MessageRole
from pepperpy.llm import LLMProvider


class MockLLMProvider(LLMProvider):
    """A mock LLM provider for demonstration purposes."""

    def __init__(
        self, name: str = "mock", config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize the provider."""
        super().__init__(name=name, config=config or {})

    async def initialize(self) -> None:
        """Initialize the provider."""
        print("Initializing mock LLM provider")
        self.initialized = True

    async def generate(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate a response from the provided messages.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options

        Returns:
            Generation result
        """
        # Convert string to message list if needed
        if isinstance(messages, str):
            msg_list = [Message(role=MessageRole.USER, content=messages)]
        else:
            msg_list = messages

        # Print the received messages for demonstration
        for msg in msg_list:
            print(f"Message ({msg.role}): {msg.content}")

        # Return a mock response
        return GenerationResult(
            content="This is a mock response from the LLM provider.",
            messages=msg_list,
            usage={"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
        )

    async def stream(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Generate text in a streaming fashion.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options

        Returns:
            AsyncIterator yielding GenerationChunk objects
        """
        # Just yield a single chunk for simplicity
        yield GenerationChunk(
            content="This is a mock streaming response.", finish_reason="stop"
        )

    async def cleanup(self) -> None:
        """Clean up resources."""
        print("Cleaning up mock LLM provider")


async def main() -> None:
    """Run the example."""
    print("Minimal Example")
    print("=" * 50)

    # Create a PepperPy instance
    pepper = pepperpy.PepperPy()

    # Create and set the mock provider
    mock_provider = MockLLMProvider()
    pepper._llm = mock_provider  # This would normally be done with with_llm()

    # Use the async context manager
    async with pepper:
        # Create a message
        messages = [Message(role=MessageRole.USER, content="Hello, PepperPy!")]

        # Get a response
        print("\nSending message...")
        response = await pepper.llm.generate(messages)

        # Print the response
        print(f"\nResponse: {response.content}")
        print(
            f"Tokens: {response.usage.get('total_tokens', 0) if response.usage else 0}"
        )


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
