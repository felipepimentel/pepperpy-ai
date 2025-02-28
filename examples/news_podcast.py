"""News Podcast Generator Example.

This example demonstrates how to create a news podcast generator using Pepperpy.
It shows how to:
1. Fetch news articles from RSS feeds
2. Convert text to speech
3. Generate audio files

Prerequisites:
  - Python 3.12+
  - pip install pepperpy

Quick Start:
  ```bash
  # Install and run
  pip install pepperpy
  python examples/news_podcast.py
  ```
"""

import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union
from uuid import uuid4

from pepperpy.core.common.messages import ProviderMessage, ProviderResponse
from pepperpy.core.common.providers.base import BaseProvider, ProviderConfig
from pepperpy.providers.llm.base import (
    LLMConfig,
    LLMMessage,
    LLMResponse,
)
from pepperpy.providers.llm.openai import OpenAIProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Test data
TEST_ARTICLES = [
    {
        "title": "New AI Breakthrough",
        "description": "Scientists announce major progress in AI research.",
        "link": "https://example.com/ai-news",
        "published": "2024-02-21T12:00:00Z",
        "source": "Tech News",
    },
    {
        "title": "Climate Change Update",
        "description": "Latest findings on global climate patterns.",
        "link": "https://example.com/climate",
        "published": "2024-02-21T11:30:00Z",
        "source": "Science Daily",
    },
    {
        "title": "Space Exploration News",
        "description": "New discoveries from deep space missions.",
        "link": "https://example.com/space",
        "published": "2024-02-21T11:00:00Z",
        "source": "Space News",
    },
]


class TestArticle:
    """Test article data structure."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize test article."""
        self.title = kwargs.get("title", "")
        self.description = kwargs.get("description", "")
        self.link = kwargs.get("link", "")
        self.published = kwargs.get("published", "")
        self.source = kwargs.get("source", "")

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.title} - {self.description}"


# Test script template
TEST_SCRIPT = """
Welcome to today's news update!

Here are the top stories:

{stories}

That's all for today's news. Thanks for listening!
"""

# Test audio data
TEST_AUDIO = b"This is simulated audio data"


class CustomRSSProvider(BaseProvider):
    """Custom RSS provider for news fetching."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the provider."""
        config = ProviderConfig(
            type="rss",
            config=kwargs,
        )
        super().__init__(config=config)
        self.sources = kwargs.get("sources", [])
        self.language = kwargs.get("language", "pt-BR")
        self.max_items = kwargs.get("max_items", 10)
        self.timeout = kwargs.get("timeout", 30.0)

    async def initialize(self) -> None:
        """Initialize the provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

    async def validate(self) -> None:
        """Validate provider configuration."""
        if not self.sources:
            raise ValueError("No RSS sources configured")
        if not self.language:
            raise ValueError("Language not specified")
        if self.max_items <= 0:
            raise ValueError("max_items must be positive")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

    async def process_message(
        self,
        message: ProviderMessage,
    ) -> Union[ProviderResponse, AsyncGenerator[ProviderResponse, None]]:
        """Process a provider message."""
        return ProviderResponse(
            content=str(TEST_ARTICLES[: self.max_items]),
            metadata={"provider_type": "rss"},
            provider_type="rss",
        )

    async def fetch(
        self, limit: int = 5, since: datetime | None = None, filters: dict | None = None
    ) -> List[Any]:
        """Fetch news articles.

        Args:
            limit: Maximum number of articles
            since: Only fetch articles since this time
            filters: Optional filters

        Returns:
            List of articles
        """
        logger.info("Fetching test articles")
        articles = [TestArticle(**article) for article in TEST_ARTICLES[:limit]]
        return articles


class CustomLocalProvider(BaseProvider):
    """Custom local provider for caching."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the provider."""
        config = ProviderConfig(
            type="local",
            config=kwargs,
        )
        super().__init__(config=config)
        self.path = kwargs.get("path", "~/.pepperpy/news_podcast")
        self.max_size = kwargs.get("max_size", "1GB")
        self.sync_interval = kwargs.get("sync_interval", 60.0)
        self.compression = kwargs.get("compression", True)

    async def initialize(self) -> None:
        """Initialize the provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

    async def validate(self) -> None:
        """Validate provider configuration."""
        if not self.path:
            raise ValueError("Cache path not specified")
        if not self.max_size:
            raise ValueError("Cache max size not specified")
        if self.sync_interval <= 0:
            raise ValueError("sync_interval must be positive")

    async def process_message(
        self,
        message: ProviderMessage,
    ) -> Union[ProviderResponse, AsyncGenerator[ProviderResponse, None]]:
        """Process a provider message."""
        return ProviderResponse(
            content="",
            metadata={"provider_type": "local"},
            provider_type="local",
        )

    async def exists(self, key: str) -> bool:
        """Mock exists implementation for test mode."""
        return False

    async def get(self, key: str) -> Any:
        """Mock get implementation for test mode."""
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expires_in: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Mock set implementation for test mode."""
        pass


class CustomGTTSProvider(BaseProvider):
    """Custom gTTS provider for speech synthesis."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the provider."""
        config = ProviderConfig(
            type="gtts",
            config=kwargs,
        )
        super().__init__(config=config)
        self.language = kwargs.get("language", "pt-BR")
        self.format = kwargs.get("format", "mp3")
        self.sample_rate = kwargs.get("sample_rate", 24000)
        self.bit_depth = kwargs.get("bit_depth", 16)
        self.channels = kwargs.get("channels", 1)

    async def initialize(self) -> None:
        """Initialize the provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

    async def validate(self) -> None:
        """Validate provider configuration."""
        if not self.language:
            raise ValueError("Language not specified")
        if not self.format:
            raise ValueError("Audio format not specified")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if self.bit_depth <= 0:
            raise ValueError("bit_depth must be positive")
        if self.channels <= 0:
            raise ValueError("channels must be positive")

    async def process_message(
        self,
        message: ProviderMessage,
    ) -> Union[ProviderResponse, AsyncGenerator[ProviderResponse, None]]:
        """Process provider message."""
        return ProviderResponse(
            content=TEST_AUDIO.decode("utf-8"),
            metadata={"provider_type": "gtts"},
            provider_type="gtts",
        )

    async def synthesize(
        self,
        text: str,
        language: str | None = None,
        voice: str | None = None,
        normalize: bool = True,
        target_db: float = -16.0,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
    ) -> bytes:
        """Mock synthesize implementation for test mode."""
        return TEST_AUDIO

    async def save(self, audio_data: bytes, output_path: Path) -> Path:
        """Mock save implementation for test mode."""
        # Create an empty file for testing
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        return output_path


class CustomOpenAIProvider(OpenAIProvider):
    """Custom OpenAI provider."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize provider."""
        config = LLMConfig(
            type="openai",
            model="gpt-4",
            temperature=0.7,
            max_tokens=2048,
        )
        super().__init__(config=config)

    async def initialize(self) -> None:
        """Initialize provider."""
        # Set test API key
        os.environ["OPENAI_API_KEY"] = "test-key"
        await super().initialize()
        logger.info("OpenAI provider initialized")

    async def cleanup(self) -> None:
        """Clean up provider."""
        await super().cleanup()
        logger.info("OpenAI provider cleaned up")

    async def generate(
        self,
        messages: List[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response using the OpenAI API.

        Args:
            messages: List of messages for context
            **kwargs: Additional parameters to pass to the API

        Returns:
            Model response
        """
        articles = [TestArticle(**article) for article in TEST_ARTICLES]
        stories = "\n".join(
            f"- {article.title}: {article.description}" for article in articles
        )
        script = TEST_SCRIPT.format(stories=stories)
        return LLMResponse(
            id=uuid4(),
            content=script,
            model="gpt-4",
            usage={
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
            finish_reason="stop",
        )


class NewsPodcastGenerator:
    """News podcast generator."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """Initialize generator.

        Args:
            output_dir: Directory to save output files
        """
        logger.info("Initializing news podcast generator...")

        # Set output directory
        self.output_dir = output_dir or Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize providers
        self.content = CustomRSSProvider(
            sources=["https://example.com/feed"],
            language="pt-BR",
            max_items=5,
        )
        self.cache = CustomLocalProvider(
            path=str(self.output_dir / "cache"),
            max_size="1GB",
        )
        self.tts = CustomGTTSProvider(
            language="pt-BR",
            format="mp3",
        )
        self.script = CustomOpenAIProvider()

    async def initialize(self) -> None:
        """Initialize all providers."""
        await self.content.initialize()
        await self.cache.initialize()
        await self.tts.initialize()
        await self.script.initialize()

    async def cleanup(self) -> None:
        """Clean up all providers."""
        await self.content.cleanup()
        await self.cache.cleanup()
        await self.tts.cleanup()
        await self.script.cleanup()

    async def generate_podcast(self) -> Path:
        """Generate a news podcast.

        Returns:
            Path to the generated audio file
        """
        try:
            # Fetch news articles
            articles = await self.content.fetch(limit=5)
            logger.info("Fetched %d articles", len(articles))

            # Generate script
            messages = [
                LLMMessage(
                    role="user",
                    content=str(articles),
                )
            ]
            response = await self.script.generate(messages)
            script = response.content
            logger.info("Generated script")

            # Convert to speech
            audio_data = await self.tts.synthesize(script)
            logger.info("Generated audio")

            # Save output
            output_path = (
                self.output_dir / f"news_podcast_{datetime.now().isoformat()}.mp3"
            )
            await self.tts.save(audio_data, output_path)
            logger.info("Saved podcast to %s", output_path)

            return output_path

        except Exception as e:
            logger.error("Failed to generate podcast: %s", e)
            raise


async def main() -> None:
    """Run the example."""
    # Create generator
    generator = NewsPodcastGenerator(output_dir=Path("test_output"))

    try:
        # Initialize
        await generator.initialize()

        # Generate podcast
        output_path = await generator.generate_podcast()
        print(f"Generated podcast: {output_path}")

    finally:
        # Clean up
        await generator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
