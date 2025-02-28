"""Story creation example.

This example demonstrates using Pepperpy to create stories with OpenAI.
It includes:
- Provider initialization
- Story generation
- Error handling

Requirements:
- Python 3.12+
- Pepperpy library
- OpenAI API key (set as OPENAI_API_KEY environment variable)

Usage:
    export OPENAI_API_KEY=your_api_key
    poetry run python examples/story_creation.py
"""

import asyncio
import logging
import os
from typing import Any, List, Optional, cast
from uuid import uuid4

from pepperpy.core.common.errors import ConfigurationError
from pepperpy.core.common.logging import get_logger
from pepperpy.providers import registry
from pepperpy.providers.base import ProviderConfig, ProviderError
from pepperpy.llm.base import (
    LLMProvider as BaseLLMProvider,
    LLMConfig,
    Message as LLMMessage,
    ProviderResponse as LLMResponse,
)

# Configure logging
logger = get_logger(__name__)

# Test cases
TEST_CASES = [
    {
        "theme": "space exploration",
        "genre": "science fiction",
        "prompt": "A story about humanity's first interstellar colony",
    },
    {
        "theme": "magical forest",
        "genre": "fantasy",
        "prompt": "A tale of a young druid discovering ancient magic",
    },
    {
        "theme": "detective mystery",
        "genre": "noir",
        "prompt": "A case involving a missing quantum computer",
    },
]

# Test API key (for demonstration only)
TEST_API_KEY = "sk-test-key"


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize mock provider."""
        # Convert ProviderConfig to LLMConfig
        llm_config = LLMConfig(
            type=config.type,
            model=config.config.get("model", "mock-model"),
            temperature=config.config.get("temperature", 0.7),
            max_tokens=config.config.get("max_tokens", 2000),
        )
        super().__init__(llm_config)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        self._initialized = True
        logger.info("Mock provider initialized")

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        self._initialized = False
        logger.info("Mock provider cleaned up")

    async def validate(self) -> None:
        """Validate provider configuration."""
        if not self.model:
            raise ConfigurationError("Model not specified")

    async def generate(
        self,
        messages: List[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a mock response."""
        try:
            # Extract prompt from messages
            prompt = next(msg.content for msg in messages if msg.role == "user")
            system_msg = next(msg.content for msg in messages if msg.role == "system")

            # Create mock story
            story = (
                f"[Test Story]\n"
                f"System: {system_msg}\n"
                f"Prompt: {prompt}\n"
                "This is a test story generated without using the OpenAI API."
            )

            return LLMResponse(
                id=uuid4(),
                content=story,
                model=self.model,
                usage={
                    "prompt_tokens": 100,
                    "completion_tokens": 100,
                    "total_tokens": 200,
                },
                finish_reason="stop",
            )
        except Exception as e:
            logger.error(
                "Failed to generate response",
                extra={"error": str(e), "messages": messages},
                exc_info=True,
            )
            raise ProviderError(f"Failed to generate response: {e}")

    async def get_token_count(self, text: str) -> int:
        """Get mock token count."""
        return len(text.split())


class StoryGenerator:
    """Story generator using OpenAI."""

    def __init__(
        self,
        output_dir: str = "stories",
        language: str = "en",
        max_length: int = 2000,
    ) -> None:
        """Initialize story generator.

        Args:
            output_dir: Directory to save stories
            language: Story language
            max_length: Maximum story length in tokens
        """
        self.output_dir = output_dir
        self.language = language
        self.max_length = max_length
        self._provider: Optional[BaseLLMProvider] = None

    async def initialize(self) -> None:
        """Initialize the generator.

        Raises:
            ConfigurationError: If initialization fails
        """
        try:
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)

            # Set test API key if not provided
            if not os.getenv("OPENAI_API_KEY"):
                os.environ["OPENAI_API_KEY"] = TEST_API_KEY

            # Create provider configuration
            config = {
                "type": "mock",
                "config": {
                    "model": "mock-model",
                    "temperature": 0.7,
                    "max_tokens": self.max_length,
                },
            }

            # Register and get mock provider
            if os.getenv("OPENAI_API_KEY") == TEST_API_KEY:
                registry.register_provider("mock", MockLLMProvider)
                provider = await registry.get_provider("mock", config)
            else:
                provider = await registry.get_provider("openai", config)

            self._provider = cast(BaseLLMProvider, provider)
            logger.info("Story generator initialized")

        except Exception as e:
            logger.error(
                "Failed to initialize story generator",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise ConfigurationError(f"Failed to initialize story generator: {e}")

    async def validate(self) -> None:
        """Validate generator configuration.

        Raises:
            ConfigurationError: If validation fails
        """
        if not os.path.isdir(self.output_dir):
            raise ConfigurationError(f"Output directory not found: {self.output_dir}")
        if not self._provider:
            raise ConfigurationError("Provider not initialized")

    async def create_story(
        self,
        theme: str,
        genre: str,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Create a story.

        Args:
            theme: Story theme
            genre: Story genre
            prompt: Story prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated story

        Raises:
            ProviderError: If story creation fails
        """
        try:
            # Validate state
            await self.validate()

            # Create system message
            system_msg = (
                f"You are a creative writer specializing in {genre} stories. "
                f"Write an engaging story in {self.language} based on the theme: {theme}. "
                "The story should be well-structured with a clear beginning, middle, and end. "
                "Use descriptive language and dialogue to bring the story to life."
            )

            # Create messages
            messages = [
                LLMMessage(role="system", content=system_msg),
                LLMMessage(role="user", content=prompt),
            ]

            # Generate story
            if not self._provider:
                raise ConfigurationError("Provider not initialized")

            # Generate story using provider
            response = await self._provider.generate(messages, **kwargs)
            story = response.content.strip()

            # Save story
            story_id = str(uuid4())
            story_filename = f"{story_id}.txt"
            filepath = os.path.join(self.output_dir, story_filename)
            with open(filepath, "w") as f:
                f.write(story)

            logger.info(
                "Story created",
                extra={
                    "theme": theme,
                    "genre": genre,
                    "story_filename": story_filename,
                    "tokens": response.usage["total_tokens"],
                },
            )

            return story

        except Exception as e:
            logger.error(
                "Failed to create story",
                extra={
                    "theme": theme,
                    "genre": genre,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise ProviderError(f"Failed to create story: {e}")


async def main() -> None:
    """Run the story creation example."""
    try:
        # Initialize generator
        generator = StoryGenerator()
        await generator.initialize()

        # Generate test stories
        for case in TEST_CASES:
            try:
                story = await generator.create_story(**case)
                print(f"\nGenerated story for {case['theme']}:")
                print("-" * 80)
                print(story)
                print("-" * 80)
            except Exception as e:
                logger.error(
                    "Failed to generate story",
                    extra={"theme": case["theme"], "error": str(e)},
                    exc_info=True,
                )

    except Exception as e:
        logger.error(
            "Story creation example failed", extra={"error": str(e)}, exc_info=True
        )
    finally:
        # Cleanup
        await registry.cleanup()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
