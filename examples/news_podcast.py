"""Example of using Pepperpy to create a news-to-podcast generator."""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from pepperpy.content import BaseContentProvider, ContentItem
from pepperpy.core.config import Configuration
from pepperpy.llm import BaseLLMProvider
from pepperpy.memory import BaseMemoryProvider
from pepperpy.synthesis import BaseSynthesisProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsPodcastGenerator:
    """Generates podcasts from news articles."""

    def __init__(
        self, config_path: Optional[Path] = None, output_dir: Optional[Path] = None
    ):
        """Initialize the generator.

        Args:
            config_path: Optional path to configuration file
            output_dir: Optional directory for output files
        """
        self.config = Configuration(config_path)
        self.output_dir = output_dir or Path.home() / ".pepperpy" / "podcasts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load providers
        self.content_provider = self.config.load_provider(
            "content", "default", BaseContentProvider
        )
        self.llm_provider = self.config.load_provider("llm", "default", BaseLLMProvider)
        self.synthesis_provider = self.config.load_provider(
            "synthesis", "default", BaseSynthesisProvider
        )
        self.memory_provider = self.config.load_provider(
            "memory", "default", BaseMemoryProvider
        )

    async def fetch_news(self, limit: int = 5) -> List[ContentItem]:
        """Fetch recent news articles.

        Args:
            limit: Maximum number of articles to fetch

        Returns:
            List of news articles
        """
        logger.info("Fetching news articles...")
        return await self.content_provider.fetch(limit=limit)

    async def generate_script(self, articles: List[ContentItem]) -> str:
        """Generate podcast script from articles.

        Args:
            articles: List of news articles

        Returns:
            Generated podcast script
        """
        logger.info("Generating podcast script...")

        # Create prompt
        prompt = "Generate a podcast script from these news articles:\n\n"
        for article in articles:
            prompt += f"Title: {article.title}\n"
            prompt += f"Content: {article.content}\n\n"
        prompt += "\nCreate an engaging podcast script that:"
        prompt += "\n- Has a clear introduction and conclusion"
        prompt += "\n- Presents each news story naturally"
        prompt += "\n- Uses transitions between stories"
        prompt += "\n- Has a conversational tone"
        prompt += "\n- Is in Brazilian Portuguese"

        # Generate script
        return await self.llm_provider.generate(prompt)

    async def create_podcast(self, script: str) -> Path:
        """Create podcast audio from script.

        Args:
            script: Podcast script to synthesize

        Returns:
            Path to generated audio file
        """
        logger.info("Creating podcast audio...")

        # Generate audio
        audio_data = await self.synthesis_provider.synthesize(script, language="pt-BR")

        # Save file
        output_path = self.output_dir / f"podcast_{asyncio.get_event_loop().time()}.mp3"
        return await self.synthesis_provider.save(audio_data, output_path)

    async def generate(self) -> Path:
        """Generate a complete news podcast.

        Returns:
            Path to generated podcast file
        """
        # Fetch articles
        articles = await self.fetch_news()

        # Generate script
        script = await self.generate_script(articles)

        # Create podcast
        return await self.create_podcast(script)


async def main():
    """Run the example."""
    generator = NewsPodcastGenerator()
    podcast_path = await generator.generate()
    logger.info(f"Generated podcast: {podcast_path}")


if __name__ == "__main__":
    asyncio.run(main())
