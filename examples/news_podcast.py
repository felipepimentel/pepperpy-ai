#!/usr/bin/env python3
"""News Podcast Generator Example

Purpose:
    Demonstrate how to create an AI-powered news podcast generator using PepperPy's
    powerful pipeline capabilities:
    - Content retrieval (RSS feeds)
    - Text summarization (LLM)
    - Text-to-speech synthesis
    - Audio processing

Requirements:
    - Python 3.10+
    - PepperPy library
    - Internet connection (for RSS feeds)

Usage:
    1. Install dependencies:
       poetry install

    2. Run the example:
       poetry run python examples/news_podcast.py
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings

from pepperpy.content import RSSFeed, RSSProcessor
from pepperpy.llm import ChatMessage, ChatOptions, ChatSession, LLMProvider
from pepperpy.multimodal.audio import OutputProcessor
from pepperpy.multimodal.synthesis import TextToSpeechProvider
from pepperpy.providers import get_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PodcastConfig(BaseSettings):
    """Configuration for the news podcast generator.

    Attributes:
        feed_url: URL of the RSS feed
        output_path: Path to save the podcast
        max_articles: Maximum number of articles to include
        voice_name: Voice name or language code
    """

    feed_url: str = Field(
        default="https://news.google.com/rss", description="URL of the RSS feed"
    )
    output_path: str = Field(
        default="example_output/news_podcast.mp3",
        description="Path to save the podcast",
    )
    max_articles: int = Field(
        default=5, description="Maximum number of articles to include"
    )
    voice_name: str = Field(default="en", description="Voice name or language code")

    class Config:
        """Pydantic configuration."""

        env_prefix = "NEWS_PODCAST_"
        env_file = ".env"
        env_file_encoding = "utf-8"


async def generate_podcast(config: PodcastConfig) -> Optional[Path]:
    """Generate a news podcast using PepperPy's AI pipeline.

    Args:
        config: Podcast configuration

    Returns:
        Path to the generated podcast file or None if generation failed
    """
    logger.info("Starting news podcast generation")

    try:
        # Step 1: Create output directory
        output_path = Path(config.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Step 2: Initialize providers using PepperPy's provider registry
        # The framework handles API keys and provider configuration
        llm_provider: LLMProvider = get_provider("llm", provider_type="openai")
        tts_provider: TextToSpeechProvider = get_provider(
            "synthesis.tts", preferred_provider="elevenlabs", fallback_provider="gtts"
        )
        audio_processor: OutputProcessor = get_provider("audio.output")

        # Step 3: Fetch news articles using PepperPy's RSS processor
        logger.info(f"Fetching news from {config.feed_url}")
        rss_processor = RSSProcessor(max_articles=config.max_articles)
        feed: RSSFeed = await rss_processor.process(config.feed_url)

        if not feed.articles:
            logger.error("No articles found")
            return None

        logger.info(f"Fetched {len(feed.articles)} articles")

        # Step 4: Process each article
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_files = []

            for i, article in enumerate(feed.articles):
                # Summarize article using PepperPy's LLM module
                logger.info(f"Summarizing article: {article.title}")

                # Create a chat session for summarization
                session = ChatSession(
                    provider=llm_provider,
                    options=ChatOptions(
                        model="gpt-3.5-turbo", temperature=0.7, max_tokens=150
                    ),
                )

                # Add system message to guide the summarization
                session.add_message(
                    ChatMessage(
                        role="system",
                        content=(
                            "You are a professional news summarizer. Create a concise "
                            "summary of the news article in a style suitable for a podcast. "
                            "Keep it under 100 words."
                        ),
                    )
                )

                # Add user message with article content
                session.add_message(
                    ChatMessage(
                        role="user",
                        content=(
                            f"Title: {article.title}\n\n"
                            f"Summary: {article.summary}\n\n"
                            f"Link: {article.link}"
                        ),
                    )
                )

                # Generate summary
                response = await session.generate_response()
                summary = response.content

                # Convert summary to speech using PepperPy's synthesis module
                logger.info("Converting summary to speech")
                audio_path = Path(temp_dir) / f"article_{i}.mp3"

                await tts_provider.synthesize(
                    text=summary, output_path=audio_path, voice=config.voice_name
                )

                audio_files.append(audio_path)

            # Combine audio files using PepperPy's audio processing module
            logger.info(f"Combining {len(audio_files)} audio segments")

            # Create a podcast with intro and outro
            podcast = await audio_processor.combine(
                audio_files=audio_files,
                output_path=output_path,
                add_intro=True,
                add_outro=True,
            )

            logger.info(f"Podcast generated successfully: {podcast}")
            return podcast

    except Exception as e:
        logger.error(f"Error generating podcast: {e}")
        return None


async def main() -> None:
    """Run the news podcast example."""
    try:
        # Load configuration from environment variables
        config = PodcastConfig()

        # Generate podcast
        podcast_path = await generate_podcast(config)

        if podcast_path:
            print(f"\nPodcast generated successfully! 🎉")
            print(f"Location: {podcast_path}")
        else:
            print("\nFailed to generate podcast. Check logs for details.")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
