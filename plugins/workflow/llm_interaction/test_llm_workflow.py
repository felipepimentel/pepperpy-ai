"""Test script for LLM interaction workflow."""

import asyncio
import json
import logging
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self, model_id: str = "mock-model") -> None:
        """Initialize the mock provider.

        Args:
            model_id: Model identifier
        """
        self.model_id = model_id
        self.initialized = False
        logger.info(f"Created mock LLM provider with model {model_id}")

    async def initialize(self) -> None:
        """Initialize the provider."""
        self.initialized = True
        logger.info("Initialized mock LLM provider")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.initialized = False
        logger.info("Cleaned up mock LLM provider")

    async def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt.

        Args:
            prompt: The prompt to generate from
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        # Return mock response based on prompt
        if "weather" in prompt.lower():
            return "The weather today is sunny with a high of 75°F."
        elif "news" in prompt.lower():
            return "The latest news includes advancements in AI technology and space exploration."
        elif "recipe" in prompt.lower():
            return "Here's a simple pasta recipe: 1. Boil pasta. 2. Prepare sauce. 3. Mix and serve."
        else:
            return f"This is a mock response to: {prompt}"

    async def chat_completion(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> dict[str, Any]:
        """Generate chat completion.

        Args:
            messages: List of messages
            **kwargs: Additional parameters

        Returns:
            Chat completion response
        """
        # Extract the last user message
        last_message = next(
            (msg["content"] for msg in reversed(messages) if msg.get("role") == "user"),
            "No user message found",
        )

        # Generate a response
        response_text = await self.generate_text(last_message)

        return {
            "model": self.model_id,
            "choices": [{"message": {"role": "assistant", "content": response_text}}],
            "usage": {
                "prompt_tokens": len(json.dumps(messages)),
                "completion_tokens": len(response_text),
                "total_tokens": len(json.dumps(messages)) + len(response_text),
            },
        }


class LLMWorkflow:
    """Simple LLM interaction workflow."""

    def __init__(self, provider: Any = None) -> None:
        """Initialize the workflow.

        Args:
            provider: LLM provider
        """
        self.provider = provider or MockLLMProvider()
        self.initialized = False
        self.conversation_history = []

    async def initialize(self) -> None:
        """Initialize the workflow."""
        if not self.initialized:
            await self.provider.initialize()
            self.initialized = True
            logger.info("Initialized LLM workflow")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.initialized:
            await self.provider.cleanup()
            self.initialized = False
            logger.info("Cleaned up LLM workflow")

    async def generate_completion(self, prompt: str) -> dict[str, Any]:
        """Generate text completion.

        Args:
            prompt: The prompt to complete

        Returns:
            Completion result
        """
        if not self.initialized:
            await self.initialize()

        try:
            response = await self.provider.generate_text(prompt)
            return {"status": "success", "result": response, "prompt": prompt}
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            return {"status": "error", "error": str(e), "prompt": prompt}

    async def chat(
        self, message: str, system_prompt: str | None = None
    ) -> dict[str, Any]:
        """Process a chat message.

        Args:
            message: User message
            system_prompt: Optional system prompt

        Returns:
            Chat response
        """
        if not self.initialized:
            await self.initialize()

        # Prepare messages
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        messages.extend(self.conversation_history)

        # Add user message
        messages.append({"role": "user", "content": message})

        try:
            # Generate response
            response = await self.provider.chat_completion(messages)

            # Extract response content
            assistant_message = response["choices"][0]["message"]

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append(assistant_message)

            return {
                "status": "success",
                "result": assistant_message["content"],
                "full_response": response,
            }
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {"status": "error", "error": str(e)}


async def test_text_completion() -> None:
    """Test text completion functionality."""
    # Create workflow
    workflow = LLMWorkflow()

    try:
        # Initialize
        await workflow.initialize()

        # Test different prompts
        prompts = [
            "What's the weather like today?",
            "Tell me about the latest news",
            "Give me a simple recipe",
        ]

        print("\n🔤 TESTING TEXT COMPLETION\n")

        for prompt in prompts:
            print(f"\n📝 Prompt: {prompt}")
            result = await workflow.generate_completion(prompt)

            if result["status"] == "success":
                print(f"✅ Response: {result['result']}")
            else:
                print(f"❌ Error: {result['error']}")

    finally:
        # Clean up
        await workflow.cleanup()


async def test_chat_conversation() -> None:
    """Test chat conversation functionality."""
    # Create workflow
    workflow = LLMWorkflow()
    system_prompt = "You are a helpful AI assistant that specializes in technology."

    try:
        # Initialize
        await workflow.initialize()

        print("\n💬 TESTING CHAT CONVERSATION\n")
        print(f"System prompt: {system_prompt}\n")

        # Simulate a conversation
        messages = [
            "Hello, who are you?",
            "Can you tell me about AI technologies?",
            "What are the advantages of using LLMs?",
        ]

        for i, message in enumerate(messages):
            print(f"\n🧑 User ({i + 1}):")
            print(f"  {message}")

            result = await workflow.chat(message, system_prompt if i == 0 else None)

            if result["status"] == "success":
                print("\n🤖 Assistant:")
                print(f"  {result['result']}")
            else:
                print(f"\n❌ Error: {result['error']}")

    finally:
        # Clean up
        await workflow.cleanup()


async def main() -> None:
    """Run the tests."""
    print("\n🔍 LLM INTERACTION WORKFLOW TEST\n")

    # Test text completion
    await test_text_completion()

    # Test chat functionality
    await test_chat_conversation()


if __name__ == "__main__":
    asyncio.run(main())
