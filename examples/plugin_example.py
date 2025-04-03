#!/usr/bin/env python
"""
Example demonstrating how to create custom plugins in PepperPy.

This shows how to create and register custom plugins
that extend the core functionality of the framework.
"""

import asyncio
from typing import Any, Dict, List


# Mock classes and functionality
class Message:
    """Simple message class for demonstration."""

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class MessageRole:
    """Message role constants."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class MockPepperpyPlugin:
    """Base class for all PepperPy plugins."""

    def __init__(self, **kwargs):
        self.config = kwargs
        self.initialized = False

        # Bind config to instance attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def initialize(self) -> None:
        """Initialize the plugin."""
        if self.initialized:
            return

        print(f"Initializing {self.__class__.__name__} with config: {self.config}")
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        print(f"Cleaning up {self.__class__.__name__}")
        self.initialized = False

    # Context manager support
    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


# Custom plugin implementation
class CustomLLMPlugin(MockPepperpyPlugin):
    """Custom LLM plugin implementation."""

    async def generate(self, messages: List[Message], **kwargs) -> Dict[str, Any]:
        """Generate text based on messages."""
        if not self.initialized:
            await self.initialize()

        print(f"Generating with {self.__class__.__name__}...")

        # Find the last user message
        user_messages = [m for m in messages if m.role == MessageRole.USER]
        if not user_messages:
            return {"content": "No user message found."}

        last_message = user_messages[-1].content

        # Simple response generation
        if "hello" in last_message.lower():
            return {"content": "Hello! I'm your custom LLM plugin."}
        else:
            return {
                "content": f"You said: {last_message}. This is a response from CustomLLMPlugin."
            }


async def register_and_use_plugin():
    """Demonstrate plugin registration and usage."""
    print("\n=== Plugin Registration and Usage ===")

    # Create plugin instance
    plugin = CustomLLMPlugin(model="custom-model", temperature=0.7)

    # Use with context manager
    async with plugin:
        # Create test messages
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            Message(role=MessageRole.USER, content="Hello, custom plugin!"),
        ]

        # Generate response
        response = await plugin.generate(messages)
        print(f"Response: {response['content']}")

        # Another example
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            Message(role=MessageRole.USER, content="What can you do?"),
        ]

        response = await plugin.generate(messages)
        print(f"Response: {response['content']}")


async def main():
    """Run the example."""
    print("=== PepperPy Plugin Example ===")

    await register_and_use_plugin()

    print("\nPlugin example completed!")


if __name__ == "__main__":
    asyncio.run(main())
