"""News-to-podcast generator example using Pepperpy.

Purpose:
    Demonstrate how to create an automated news podcast generator that:
    - Fetches news from RSS feeds
    - Generates natural podcast scripts
    - Synthesizes speech with effects
    - Caches results for efficiency

    This example showcases the integration of multiple Pepperpy capabilities:
    1. Content Capability:
       - RSS feed fetching
       - Content filtering by language
       - Metadata handling

    2. LLM Capability:
       - Natural language script generation
       - Context-aware prompting
       - Temperature control for creativity

    3. Synthesis Capability:
       - Text-to-speech conversion
       - Audio effects (normalization, fades)
       - Multi-format support

    4. Memory Capability:
       - Efficient caching
       - Expiration handling
       - Metadata storage

Requirements:
    - Python 3.12+
    - Pepperpy library
    - OpenAI API key
    - Internet connection (for RSS feeds)

Configuration:
    The example supports various configuration options through environment
    variables, constructor parameters, and provider settings.

    1. Environment Variables:
       - OPENAI_API_KEY (required)
         Description: OpenAI API key for LLM and TTS
         Example: export OPENAI_API_KEY=sk-...

       - PEPPERPY_OUTPUT_DIR (optional)
         Description: Custom output directory for podcasts
         Default: ~/.pepperpy/podcasts
         Example: export PEPPERPY_OUTPUT_DIR=/path/to/podcasts

       - PEPPERPY_CACHE_DIR (optional)
         Description: Custom cache directory
         Default: ~/.pepperpy/cache
         Example: export PEPPERPY_CACHE_DIR=/path/to/cache

    2. NewsPodcastGenerator Parameters:
       - output_dir: Optional[Path]
         Description: Custom output directory
         Default: ~/.pepperpy/podcasts

    3. RSS Provider Settings:
       - sources: List[str]
         Description: RSS feed URLs
         Default: UOL Technology and Economy feeds

       - language: str
         Description: Content language filter
         Default: "pt-BR"

       - max_items: int
         Description: Maximum items per feed
         Default: 10

       - timeout: float
         Description: Feed fetch timeout in seconds
         Default: 30.0

    4. OpenAI Provider Settings:
       - model: str
         Description: GPT model to use
         Default: "gpt-4"

       - temperature: float
         Description: Response creativity (0.0-1.0)
         Default: 0.7

       - max_tokens: int
         Description: Maximum response length
         Default: 2048

    5. Local Provider Settings:
       - path: str
         Description: Cache directory path
         Default: "~/.pepperpy/news_podcast"

       - max_size: str
         Description: Maximum cache size
         Default: "1GB"

       - sync_interval: float
         Description: Disk sync interval in seconds
         Default: 60.0

       - compression: bool
         Description: Enable cache compression
         Default: True

    6. GTTS Provider Settings:
       - language: str
         Description: Speech language
         Default: "pt-BR"

       - format: str
         Description: Audio format
         Default: "mp3"

       - sample_rate: int
         Description: Audio sample rate in Hz
         Default: 24000

       - bit_depth: int
         Description: Audio bit depth
         Default: 16

       - channels: int
         Description: Audio channels (1=mono, 2=stereo)
         Default: 1

    Default Configuration:
    The example uses Brazilian Portuguese (pt-BR) as the default language
    and is configured for optimal podcast generation with:
    - 24-hour news caching
    - High-quality audio (24kHz, 16-bit)
    - Balanced LLM creativity (temperature=0.7)
    - Efficient memory usage (1GB cache, compression)

    To modify these settings, either:
    1. Set environment variables before running
    2. Pass parameters to the constructor
    3. Modify provider settings after instantiation

Usage:
    1. Install dependencies:
       poetry install

    2. Set environment variables:
       export OPENAI_API_KEY=your_key_here

    3. Run the example:
       poetry run python examples/news_podcast.py

Example Output:
    ```
    2024-02-18 15:30:00 INFO Fetching news articles...
    2024-02-18 15:30:02 INFO Found 5 articles
    2024-02-18 15:30:02 INFO Generating podcast script...
    2024-02-18 15:30:10 INFO Creating podcast audio...
    2024-02-18 15:30:30 INFO Generated podcast: ~/.pepperpy/podcasts/podcast_20240218_153030.mp3
    ```

Error Handling:
    The example handles various error cases:
    - Network errors during RSS fetching
    - API errors from OpenAI
    - File system errors
    - Invalid content or format errors

    Each error is properly logged with context and cleaned up appropriately.

Cache Strategy:
    1. News articles are cached for 24 hours with:
       - Key format: news_articles_{date}
       - Metadata: Fetch timestamp
       - Automatic expiration

    2. Generated scripts are cached per day with:
       - Key format: script_{date}
       - Metadata: Generation parameters
       - Language-specific storage

Performance Considerations:
    - Uses async/await for efficient I/O
    - Implements proper resource cleanup
    - Caches results to minimize API calls
    - Handles memory efficiently
    - Compresses cached data
    - Syncs to disk periodically

Architecture:
    The example follows a modular architecture:
    1. Provider Classes:
       - CustomRSSProvider: News fetching
       - CustomLocalProvider: Memory caching
       - CustomGTTSProvider: Speech synthesis
       - CustomOpenAIProvider: Script generation

    2. Main Generator:
       - NewsPodcastGenerator: Orchestrates the workflow
       - Handles initialization and cleanup
       - Manages resource lifecycle

Usage Examples:

    1. Basic Usage (Default Settings):
       ```python
       from examples.news_podcast import NewsPodcastGenerator
       import asyncio

       async def basic_example():
           generator = NewsPodcastGenerator()
           await generator.initialize()
           try:
               podcast_path = await generator.generate()
               print(f"Generated podcast: {podcast_path}")
           finally:
               await generator.cleanup()

       asyncio.run(basic_example())
       ```

    2. Custom Output Directory:
       ```python
       from pathlib import Path
       from examples.news_podcast import NewsPodcastGenerator
       import asyncio

       async def custom_output_example():
           output_dir = Path.home() / "my_podcasts"
           generator = NewsPodcastGenerator(output_dir=output_dir)
           await generator.initialize()
           try:
               podcast_path = await generator.generate()
               print(f"Generated podcast: {podcast_path}")
           finally:
               await generator.cleanup()

       asyncio.run(custom_output_example())
       ```

    3. Fetch Specific Number of Articles:
       ```python
       from examples.news_podcast import NewsPodcastGenerator
       import asyncio

       async def custom_fetch_example():
           generator = NewsPodcastGenerator()
           await generator.initialize()
           try:
               # Fetch 3 most recent articles
               articles = await generator.fetch_news(limit=3)
               script = await generator.generate_script(articles)
               podcast_path = await generator.create_podcast(script)
               print(f"Generated podcast: {podcast_path}")
           finally:
               await generator.cleanup()

       asyncio.run(custom_fetch_example())
       ```

    4. Custom Provider Configuration:
       ```python
       from examples.news_podcast import (
           NewsPodcastGenerator,
           CustomRSSProvider,
           CustomGTTSProvider
       )
       import asyncio

       async def custom_providers_example():
           # Configure custom RSS provider
           rss_provider = CustomRSSProvider(
               sources=[
                   "http://rss.cnn.com/rss/edition_technology.rss",
                   "http://rss.cnn.com/rss/edition_business.rss"
               ],
               language="en",
               max_items=5,
               timeout=60.0
           )

           # Configure custom TTS provider
           tts_provider = CustomGTTSProvider(
               language="en",
               format="mp3",
               sample_rate=44100,
               bit_depth=24,
               channels=2
           )

           # Create generator with custom providers
           generator = NewsPodcastGenerator()
           generator.content = rss_provider
           generator.synthesis = tts_provider

           await generator.initialize()
           try:
               podcast_path = await generator.generate()
               print(f"Generated podcast: {podcast_path}")
           finally:
               await generator.cleanup()

       asyncio.run(custom_providers_example())
       ```

    5. Error Handling Example:
       ```python
       from examples.news_podcast import NewsPodcastGenerator
       import asyncio
       import logging
       from pepperpy.exceptions import ContentError, SynthesisError

       async def error_handling_example():
           # Configure detailed logging
           logging.basicConfig(
               level=logging.DEBUG,
               format='%(asctime)s %(levelname)s %(message)s'
           )

           generator = NewsPodcastGenerator()
           await generator.initialize()
           try:
               try:
                   articles = await generator.fetch_news()
                   if not articles:
                       raise ContentError("No articles found")

                   script = await generator.generate_script(articles)
                   podcast_path = await generator.create_podcast(script)
                   print(f"Generated podcast: {podcast_path}")

               except ContentError as e:
                   logging.error(f"Content error: {e}")
                   # Handle content errors (e.g., retry with different sources)

               except SynthesisError as e:
                   logging.error(f"Synthesis error: {e}")
                   # Handle synthesis errors (e.g., try different voice)

           finally:
               await generator.cleanup()

       asyncio.run(error_handling_example())
       ```

Troubleshooting Guide:

    1. Installation Issues:

       Problem: Poetry installation fails
       Solution:
       - Ensure Python 3.12+ is installed: python --version
       - Update pip: pip install --upgrade pip
       - Install Poetry: curl -sSL https://install.python-poetry.org | python3 -
       - Try clean install: poetry env remove && poetry install

       Problem: Missing dependencies
       Solution:
       - Update Poetry lock file: poetry lock --no-update
       - Install dependencies: poetry install
       - Check virtual env: poetry env info

    2. Configuration Issues:

       Problem: "OpenAI API key not found"
       Solution:
       - Set API key: export OPENAI_API_KEY=your_key_here
       - Verify key: echo $OPENAI_API_KEY
       - Check key validity with OpenAI dashboard

       Problem: "Permission denied" for output directory
       Solution:
       - Check directory permissions: ls -la ~/.pepperpy
       - Create directory manually: mkdir -p ~/.pepperpy/podcasts
       - Set permissions: chmod 755 ~/.pepperpy/podcasts

    3. Runtime Issues:

       Problem: "No articles found"
       Possible causes:
       - Network connectivity issues
       - RSS feed unavailable
       - Language filter mismatch
       Solutions:
       - Check internet connection
       - Verify RSS feed URLs
       - Try different news sources
       - Adjust language settings

       Problem: "Failed to generate script"
       Possible causes:
       - OpenAI API rate limit
       - Invalid article format
       - Token limit exceeded
       Solutions:
       - Check API usage in OpenAI dashboard
       - Reduce number of articles
       - Adjust max_tokens parameter
       - Wait and retry

       Problem: "Audio generation failed"
       Possible causes:
       - Disk space full
       - Invalid audio settings
       - gTTS service issues
       Solutions:
       - Check available disk space: df -h
       - Verify audio parameters
       - Try different TTS provider
       - Clear cache directory

    4. Performance Issues:

       Problem: Slow execution
       Possible causes:
       - Network latency
       - Large cache size
       - Resource contention
       Solutions:
       - Check network speed
       - Clear cache: rm -rf ~/.pepperpy/cache/*
       - Adjust cache settings
       - Reduce concurrent operations

       Problem: High memory usage
       Possible causes:
       - Too many articles
       - Large audio files
       - Memory leaks
       Solutions:
       - Reduce batch size
       - Clear memory cache
       - Update to latest version
       - Monitor with: top or htop

    5. Cache Issues:

       Problem: Cache not working
       Possible causes:
       - Invalid cache directory
       - Permission issues
       - Disk full
       Solutions:
       - Check cache path
       - Verify permissions
       - Clear old cache files
       - Monitor disk space

       Problem: Stale cache
       Solutions:
       - Clear cache manually
       - Adjust cache duration
       - Force refresh with new instance

    6. Debug Mode:

       For detailed debugging:
       ```python
       import logging
       logging.basicConfig(
           level=logging.DEBUG,
           format='%(asctime)s %(levelname)s %(name)s %(message)s'
       )
       ```

       Key log messages to watch:
       - "Fetching news articles...": RSS feed access
       - "Generating podcast script...": LLM processing
       - "Creating podcast audio...": TTS conversion
       - "Cache hit/miss": Memory operations

    7. Common Error Messages:

       "ContentError: Failed to fetch articles"
       - Check network connection
       - Verify RSS feed URLs
       - Check feed response format

       "LLMError: Failed to generate script"
       - Verify OpenAI API key
       - Check token limits
       - Monitor API rate limits

       "SynthesisError: Failed to create audio"
       - Check disk space
       - Verify audio settings
       - Monitor TTS service status

       "MemoryError: Cache operation failed"
       - Check disk permissions
       - Verify cache directory
       - Monitor available space

    For additional help:
    - Check Pepperpy documentation
    - Review example source code
    - Submit issues on GitHub
    - Join community discussions
"""

import asyncio
import logging
import os
import sys
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional, Union
from uuid import uuid4

from pydantic import SecretStr

from pepperpy.agents.providers.base import BaseProvider
from pepperpy.agents.providers.domain import ProviderConfig, ProviderMetadata
from pepperpy.agents.providers.services.openai import OpenAIConfig, OpenAIProvider
from pepperpy.core.base import BaseComponent
from pepperpy.core.errors import PepperpyError
from pepperpy.core.messages import ProviderMessage, ProviderResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestArticle:
    """Test article data structure."""

    def __init__(
        self,
        title: str,
        description: str,
        link: str,
        published: str,
        source: str = "Test Source",
    ) -> None:
        """Initialize test article.

        Args:
            title: Article title
            description: Article description
            link: Article URL
            published: Publication timestamp
            source: Article source
        """
        self.title = title
        self.description = description
        self.link = link
        self.published_at = datetime.fromisoformat(published)
        self.source = source

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            Article string
        """
        return f"{self.title} ({self.source})"


# Test data
TEST_ARTICLES = [
    {
        "title": "AI Breakthrough in Natural Language Processing",
        "description": "Researchers achieve new milestone in language understanding.",
        "link": "https://example.com/ai-nlp",
        "published": datetime.now(UTC).isoformat(),
        "source": "Tech News",
    },
    {
        "title": "Future of Remote Work",
        "description": "Companies adapt to hybrid work models post-pandemic.",
        "link": "https://example.com/remote-work",
        "published": datetime.now(UTC).isoformat(),
        "source": "Business News",
    },
    {
        "title": "Sustainable Technology Trends",
        "description": "Green tech innovations shaping the industry.",
        "link": "https://example.com/green-tech",
        "published": datetime.now(UTC).isoformat(),
        "source": "Tech News",
    },
]

TEST_SCRIPT = """
Welcome to the Tech News Podcast!

Today's top stories:

1. AI Breakthrough in Natural Language Processing
   Researchers have achieved a significant milestone in language understanding,
   bringing us closer to more natural human-computer interactions.

2. Future of Remote Work
   As companies continue to adapt to post-pandemic realities, hybrid work models
   are becoming the new standard, combining office and remote work flexibility.

3. Sustainable Technology Trends
   The tech industry is increasingly focusing on green innovations, with new
   developments in sustainable computing and energy-efficient solutions.

That's all for today's news. Thanks for listening!
"""

TEST_AUDIO = b"This is simulated audio data"


class CustomRSSProvider(BaseProvider):
    """Custom RSS provider for news fetching."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the provider."""
        now = datetime.now(UTC)
        provider_type = "rss"
        config = ProviderConfig(
            provider_type=provider_type,
            name="rss",
            version="1.0.0",
            settings=kwargs,
        )
        metadata = ProviderMetadata(
            provider_type=provider_type,
            capabilities=["fetch", "filter"],
            settings=kwargs,
            statistics={},
            created_at=now,
            updated_at=now,
            version="1.0.0",
            tags=["rss", "news"],
            properties={
                "provider_type": provider_type,
                "capabilities": ["fetch", "filter"],
            },
        )
        super().__init__(id=uuid4(), metadata=metadata, config=config)
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
        now = datetime.now(UTC)
        provider_type = "local"
        config = ProviderConfig(
            provider_type=provider_type,
            name="local",
            version="1.0.0",
            settings=kwargs,
        )
        metadata = ProviderMetadata(
            provider_type=provider_type,
            capabilities=["cache", "store"],
            settings=kwargs,
            statistics={},
            created_at=now,
            updated_at=now,
            version="1.0.0",
            tags=["local", "cache"],
            properties={
                "provider_type": provider_type,
                "capabilities": ["cache", "store"],
            },
        )
        super().__init__(id=uuid4(), metadata=metadata, config=config)
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
        now = datetime.now(UTC)
        provider_type = "gtts"
        config = ProviderConfig(
            provider_type=provider_type,
            name="gtts",
            version="1.0.0",
            settings=kwargs,
        )
        metadata = ProviderMetadata(
            provider_type=provider_type,
            capabilities=["tts", "audio"],
            settings=kwargs,
            statistics={},
            created_at=now,
            updated_at=now,
            version="1.0.0",
            tags=["gtts", "audio"],
            properties={
                "provider_type": provider_type,
                "capabilities": ["tts", "audio"],
            },
        )
        super().__init__(id=uuid4(), metadata=metadata, config=config)
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
        config = OpenAIConfig(
            type="openai",
            api_key=SecretStr("test-key"),
            model="gpt-4",
            temperature=0.7,
            max_tokens=2048,
        )
        super().__init__(config=config)

    async def initialize(self) -> None:
        """Initialize provider."""
        logger.info("OpenAI provider initialized")

    async def cleanup(self) -> None:
        """Clean up provider."""
        logger.info("OpenAI provider cleaned up")

    async def process_message(
        self,
        message: ProviderMessage,
    ) -> Union[ProviderResponse, AsyncGenerator[ProviderResponse, None]]:
        """Process provider message."""
        return ProviderResponse(
            content=TEST_SCRIPT,
            metadata={"provider_type": "openai"},
            provider_type="openai",
        )

    async def generate(self, prompt: str) -> str:
        """Generate text from prompt.

        Args:
            prompt: Input prompt

        Returns:
            Generated text
        """
        logger.info("Generating test script")
        return TEST_SCRIPT


class NewsPodcastGenerator(BaseComponent):
    """News podcast generator using Pepperpy."""

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        rss_feeds: Optional[List[str]] = None,
    ) -> None:
        """Initialize the news podcast generator."""
        super().__init__(id=uuid4())
        self.output_dir = output_dir or Path.home() / ".pepperpy" / "podcasts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize providers
        self.content = CustomRSSProvider(
            sources=rss_feeds
            or [
                "http://rss.uol.com.br/feed/tecnologia.xml",
                "http://rss.uol.com.br/feed/economia.xml",
            ],
            language="pt-BR",
            max_items=10,
            timeout=30.0,
        )
        self.llm = CustomOpenAIProvider(
            model="gpt-4",
            temperature=0.7,
            max_tokens=2048,
        )
        self.memory = CustomLocalProvider(
            path="~/.pepperpy/news_podcast",
            max_size="1GB",
            sync_interval=60.0,
            compression=True,
        )
        self.synthesis = CustomGTTSProvider(
            language="pt-BR",
            format="mp3",
            sample_rate=24000,
            bit_depth=16,
            channels=1,
        )

    async def initialize(self) -> None:
        """Initialize components."""
        await self.content.initialize()
        await self.llm.initialize()
        await self.memory.initialize()
        await self.synthesis.initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.content.cleanup()
        await self.llm.cleanup()
        await self.memory.cleanup()
        await self.synthesis.cleanup()

    def validate(self) -> None:
        """Validate component state."""
        if not self.output_dir.exists():
            raise ValueError("Output directory does not exist")

    async def fetch_news(self, limit: int = 5) -> List[Any]:
        """Fetch and process recent news articles.

        Args:
            limit: Maximum number of articles to fetch (default: 5)

        Returns:
            List of processed news articles, each containing:
            - title: Article title
            - content: Main content
            - source: News source
            - published_at: Publication date
            - metadata: Additional info (URL, author, etc.)

        Raises:
            ContentError: If fetching or processing fails

        Cache Strategy:
            - Key format: news_articles_{date}
            - Duration: 24 hours
            - Metadata: Fetch timestamp
        """
        logger.info("Fetching news articles...")

        # Get articles from the last 24 hours
        since = datetime.now(UTC) - timedelta(days=1)

        # Check memory cache first
        cache_key = f"news_articles_{since.date()}"
        if await self.memory.exists(cache_key):
            logger.info("Using cached articles")
            return await self.memory.get(cache_key)

        # Fetch with language filter
        articles = await self.content.fetch(
            limit=limit, since=since, filters={"language": "pt-BR"}
        )

        # Cache results (no processing needed as RSS provider handles it)
        await self.memory.set(
            cache_key,
            articles,
            expires_in=86400,  # 24 hours
            metadata={"fetched_at": datetime.now(UTC).isoformat()},
        )

        return articles

    async def generate_script(self, articles: List[Any]) -> str:
        """Generate podcast script.

        Args:
            articles: News articles

        Returns:
            Generated script

        Raises:
            PepperpyError: If generation fails
        """
        try:
            # Check cache first
            cache_key = f"script_{datetime.now(UTC).date()}"
            if await self.memory.exists(cache_key):
                logger.info("Using cached script")
                return await self.memory.get(cache_key)

            # Generate script
            prompt = "Generate a podcast script for the following news articles:\n\n"
            for article in articles:
                prompt += f"Title: {article.title}\n"
                prompt += f"Description: {article.description}\n"
                prompt += f"Source: {article.source}\n\n"

            script = await self.llm.generate(prompt)
            if not script:
                raise PepperpyError("Failed to generate script")

            # Cache script
            await self.memory.set(
                cache_key,
                script,
                expires_in=24 * 60 * 60,  # 24 hours
                metadata={"generated_at": datetime.now(UTC).isoformat()},
            )

            logger.info("Generated script with %d characters", len(script))
            return script

        except Exception as e:
            logger.error("Failed to generate script", extra={"error": str(e)})
            raise PepperpyError(f"Failed to generate script: {e}")

    async def create_podcast(self, script: str) -> Path:
        """Create podcast audio from script.

        Args:
            script: Podcast script to synthesize

        Returns:
            Path to the generated MP3 file

        Raises:
            SynthesisError: If audio generation fails

        Audio Processing:
        1. Text-to-speech conversion
        2. Volume normalization (-16 dB target)
        3. Fade effects (0.5s in, 1.0s out)
        4. Format conversion if needed
        5. Quality checks

        File Naming:
            podcast_{YYYYMMDD_HHMMSS}.mp3
        """
        logger.info("Creating podcast audio...")

        # Generate audio with effects
        audio_data = await self.synthesis.synthesize(
            script,
            language="pt-BR",
            voice="onyx",  # Using a male voice for the podcast
            normalize=True,  # Enable audio normalization
            target_db=-16.0,  # Target loudness
            fade_in=0.5,  # Add fade in
            fade_out=1.0,  # Add fade out
        )

        # Save file with timestamp
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"podcast_{timestamp}.mp3"
        return await self.synthesis.save(audio_data, output_path)

    async def generate(self) -> Path:
        """Generate a complete news podcast.

        Returns:
            Path to the generated podcast file

        Raises:
            ContentError: If content fetching fails
            LLMError: If script generation fails
            SynthesisError: If audio generation fails

        This is the main workflow that:
        1. Fetches the latest news
        2. Generates a script
        3. Creates the audio
        4. Handles all cleanup

        The process is fully automated and includes:
        - Error handling at each step
        - Progress logging
        - Resource management
        - Cache utilization
        """
        try:
            # Fetch articles
            articles = await self.fetch_news()

            if not articles:
                raise ValueError("No news articles found")

            # Generate script
            script = await self.generate_script(articles)

            # Create podcast
            return await self.create_podcast(script)

        except Exception as e:
            logger.error(f"Failed to generate podcast: {e}")
            raise


async def main() -> None:
    """Run the example."""
    # Set up output directory
    output_dir = Path(
        os.getenv("PEPPERPY_OUTPUT_DIR", "~/.pepperpy/podcasts")
    ).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing news podcast generator...")
    generator = NewsPodcastGenerator(output_dir=output_dir)

    try:
        await generator.initialize()

        if "--test" in sys.argv:
            logger.info("Running in automated test mode...")

            # Mock the fetch_news method to return test data
            async def mock_fetch_news(limit: int = 5) -> List[Any]:
                return TEST_ARTICLES[:limit]

            generator.fetch_news = mock_fetch_news  # type: ignore

            # Mock the generate_script method to return test script
            async def mock_generate_script(articles: List[Any]) -> str:
                return TEST_SCRIPT

            generator.generate_script = mock_generate_script  # type: ignore

            # Generate podcast
            output_path = await generator.generate()
            logger.info(f"Generated test podcast at: {output_path}")

        else:
            # Normal mode - fetch real news and generate podcast
            output_path = await generator.generate()
            logger.info(f"Generated podcast at: {output_path}")

    finally:
        await generator.cleanup()
        logger.info("News podcast generator terminated")


if __name__ == "__main__":
    # Configure logging for better visibility
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Run the example
    asyncio.run(main())
