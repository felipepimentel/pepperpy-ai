#!/usr/bin/env python
"""News Podcast Generator Example.

This example demonstrates how to use PepperPy to create a news podcast:
1. Fetch news articles from an RSS feed
2. Summarize the articles using LLM
3. Convert the summaries to speech
4. Combine the audio files into a podcast

Usage:
    poetry run python -m examples.news_podcast.news_podcast --feed <feed_url> --output <output_file>
"""

import argparse
import asyncio
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import feedparser
from pydub import AudioSegment

from pepperpy.agents.base import AgentConfig, BaseAgent

# Import from PepperPy library
from pepperpy.llm.providers.base import get_llm_provider
from pepperpy.llm.providers.base.types import CompletionOptions, MessageRole
from pepperpy.multimodal.synthesis.base import VoiceConfig
from pepperpy.multimodal.synthesis.providers.google_tts import GoogleTTSProvider
from pepperpy.observability.logging import get_logger

# Configure logging
logger = get_logger("news_podcast")


class NewsArticle:
    """Represents a news article."""

    def __init__(self, title: str, link: str, summary: str, published: str):
        """Initialize a news article.

        Args:
            title: The title of the article
            link: The URL of the article
            summary: The summary of the article
            published: The publication date
        """
        self.title = title
        self.link = link
        self.summary = summary
        self.published = published


class NewsFetcherAgent(BaseAgent):
    """Agent for fetching news articles from an RSS feed."""

    def __init__(self, feed_url: str, max_articles: int = 5):
        """Initialize news fetcher agent.

        Args:
            feed_url: URL of the RSS feed
            max_articles: Maximum number of articles to fetch
        """
        config = AgentConfig(
            name="news_fetcher",
            description="Fetches news articles from an RSS feed",
            metadata={"feed_url": feed_url, "max_articles": max_articles},
        )
        super().__init__(config)
        self.feed_url = feed_url
        self.max_articles = max_articles

    async def _initialize(self) -> None:
        """Initialize the agent."""
        logger.info(f"Initializing news fetcher agent with feed: {self.feed_url}")

    async def _cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def execute(self, **kwargs: Any) -> List[NewsArticle]:
        """Fetch articles from the feed.

        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Fetching news from {self.feed_url}")
        feed = feedparser.parse(self.feed_url)

        articles = []
        for entry in feed.entries[: self.max_articles]:
            article = NewsArticle(
                title=entry.title,
                link=entry.link,
                summary=entry.get("summary", "No summary available"),
                published=entry.get("published", datetime.now().strftime("%Y-%m-%d")),
            )
            articles.append(article)

        logger.info(f"Fetched {len(articles)} articles")
        return articles


class NewsSummarizerAgent(BaseAgent):
    """Agent for summarizing news articles using LLM."""

    def __init__(
        self, provider_name: str = "openai", model_name: str = "gpt-3.5-turbo"
    ):
        """Initialize news summarizer agent.

        Args:
            provider_name: Name of the LLM provider
            model_name: Name of the model to use
        """
        config = AgentConfig(
            name="news_summarizer",
            description="Summarizes news articles using LLM",
            metadata={"provider": provider_name, "model": model_name},
        )
        super().__init__(config)
        self.provider_name = provider_name
        self.model_name = model_name
        self.provider = None

    async def _initialize(self) -> None:
        """Initialize the LLM provider."""
        logger.info(f"Initializing LLM provider: {self.provider_name}")
        self.provider = get_llm_provider(self.provider_name)
        if not self.provider:
            raise ValueError(f"Provider not found: {self.provider_name}")

    async def _cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def execute(self, article: NewsArticle) -> str:
        """Summarize a news article.

        Args:
            article: NewsArticle object

        Returns:
            Summarized article text
        """
        logger.info(f"Summarizing article: {article.title}")

        messages = [
            {
                "role": MessageRole.SYSTEM,
                "content": "You are a professional news summarizer. Create a concise summary of the news article in a style suitable for a podcast. Keep it under 100 words.",
            },
            {
                "role": MessageRole.USER,
                "content": f"Title: {article.title}\n\nSummary: {article.summary}\n\nLink: {article.link}",
            },
        ]

        options = CompletionOptions(
            model=self.model_name, temperature=0.7, max_tokens=200
        )

        # Ensure provider is initialized
        if not self.provider:
            await self.initialize()

        response = await self.provider.chat_async(messages, options=options)

        return response.content


class PodcastGeneratorAgent(BaseAgent):
    """Agent for generating a podcast from news summaries."""

    def __init__(self, voice_name: str = "en-US-Neural2-F"):
        """Initialize podcast generator agent.

        Args:
            voice_name: Name of the voice to use
        """
        config = AgentConfig(
            name="podcast_generator",
            description="Generates a podcast from news summaries",
            metadata={"voice": voice_name},
        )
        super().__init__(config)
        self.voice_name = voice_name
        self.tts_provider = None

    async def _initialize(self) -> None:
        """Initialize the TTS provider."""
        logger.info("Initializing TTS provider")
        self.tts_provider = GoogleTTSProvider()

    async def _cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def text_to_speech(self, text: str, output_path: Path) -> Path:
        """Convert text to speech.

        Args:
            text: Text to convert
            output_path: Path to save the audio file

        Returns:
            Path to the generated audio file
        """
        logger.info(f"Converting text to speech: {text[:30]}...")

        # Ensure tts_provider is initialized
        if not self.tts_provider:
            await self.initialize()

        voice_config = VoiceConfig(
            name=self.voice_name, language_code="en-US", speaking_rate=1.0, pitch=0.0
        )

        audio_data = await self.tts_provider.synthesize(
            text=text, voice=voice_config, output_format="mp3"
        )

        # Save audio data to file
        with open(output_path, "wb") as f:
            f.write(audio_data.content)

        return output_path

    def combine_audio_files(self, audio_files: List[Path], output_path: Path) -> Path:
        """Combine audio files into a single podcast.

        Args:
            audio_files: List of audio file paths
            output_path: Path to save the combined audio

        Returns:
            Path to the combined audio file
        """
        logger.info(f"Combining {len(audio_files)} audio files")

        # Create intro jingle
        intro = AudioSegment.silent(duration=1000)  # 1 second of silence

        # Combine all audio segments
        combined = intro

        for audio_file in audio_files:
            segment = AudioSegment.from_file(audio_file, format="mp3")
            combined += segment
            # Add a short pause between segments
            combined += AudioSegment.silent(duration=500)  # 0.5 seconds of silence

        # Export combined audio
        combined.export(output_path, format="mp3")

        logger.info(f"Podcast saved to {output_path}")
        return output_path

    async def execute(
        self, articles: List[NewsArticle], summaries: List[str], output_path: Path
    ) -> Path:
        """Generate a podcast from news summaries.

        Args:
            articles: List of NewsArticle objects
            summaries: List of article summaries
            output_path: Path to save the podcast

        Returns:
            Path to the generated podcast
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            audio_files = []

            # Process each article
            for i, (article, summary) in enumerate(zip(articles, summaries)):
                # Create podcast script
                script = f"Next up: {article.title}. {summary}"

                # Convert to speech
                audio_path = temp_dir_path / f"article_{i}.mp3"
                audio_file = await self.text_to_speech(script, audio_path)
                audio_files.append(audio_file)

            # Combine audio files
            return self.combine_audio_files(audio_files, output_path)


async def generate_news_podcast(
    feed_url: str,
    output_path: str,
    max_articles: int = 5,
    llm_provider: str = "openai",
    llm_model: str = "gpt-3.5-turbo",
    voice_name: str = "en-US-Neural2-F",
) -> Path:
    """Generate a news podcast from an RSS feed.

    Args:
        feed_url: URL of the RSS feed
        output_path: Path to save the podcast
        max_articles: Maximum number of articles to include
        llm_provider: Name of the LLM provider
        llm_model: Name of the model to use
        voice_name: Name of the voice to use

    Returns:
        Path to the generated podcast
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize agents
    news_fetcher = NewsFetcherAgent(feed_url, max_articles)
    news_summarizer = NewsSummarizerAgent(llm_provider, llm_model)
    podcast_generator = PodcastGeneratorAgent(voice_name)

    # Initialize all agents
    await news_fetcher.initialize()
    await news_summarizer.initialize()
    await podcast_generator.initialize()

    try:
        # Fetch articles
        articles = await news_fetcher.execute()

        # Summarize articles
        summaries = []
        for article in articles:
            summary = await news_summarizer.execute(article)
            summaries.append(summary)

        # Generate podcast
        output_file = await podcast_generator.execute(
            articles=articles, summaries=summaries, output_path=Path(output_path)
        )

        return output_file
    finally:
        # Clean up resources
        await news_fetcher.cleanup()
        await news_summarizer.cleanup()
        await podcast_generator.cleanup()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a news podcast from an RSS feed"
    )
    parser.add_argument("--feed", required=True, help="URL of the RSS feed")
    parser.add_argument("--output", required=True, help="Path to save the podcast")
    parser.add_argument(
        "--max-articles",
        type=int,
        default=5,
        help="Maximum number of articles to include",
    )
    parser.add_argument(
        "--llm-provider", default="openai", help="Name of the LLM provider"
    )
    parser.add_argument(
        "--llm-model", default="gpt-3.5-turbo", help="Name of the model to use"
    )
    parser.add_argument(
        "--voice", default="en-US-Neural2-F", help="Name of the voice to use"
    )
    return parser.parse_args()


async def main():
    """Run the example."""
    args = parse_args()

    try:
        output_file = await generate_news_podcast(
            feed_url=args.feed,
            output_path=args.output,
            max_articles=args.max_articles,
            llm_provider=args.llm_provider,
            llm_model=args.llm_model,
            voice_name=args.voice,
        )

        logger.info(f"Podcast generated successfully: {output_file}")
    except Exception as e:
        logger.error(f"Failed to generate podcast: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
