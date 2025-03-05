"""RSS format handling for PepperPy.

This module provides functionality for handling RSS feeds:
- Parsing RSS feeds
- Extracting articles and metadata
- Converting RSS data to structured formats
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

# Importar apenas BaseProcessor, já que FormatProcessor pode não existir
from pepperpy.formats.base import BaseProcessor

logger = logging.getLogger(__name__)


class RSSArticle(BaseModel):
    """Represents an article from an RSS feed.

    Attributes:
        title: Title of the article
        link: URL link to the article
        summary: Summary or description of the article
        published: Publication date and time
        author: Author of the article
        categories: List of categories or tags
        content: Full content if available
        media: Dictionary of media items (images, videos, etc.)
    """

    title: str
    link: str
    summary: str = ""
    published: Optional[datetime] = None
    author: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    content: Optional[str] = None
    media: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class RSSFeed(BaseModel):
    """Represents an RSS feed.

    Attributes:
        title: Title of the feed
        link: URL of the feed
        description: Description of the feed
        language: Language of the feed
        articles: List of articles in the feed
        last_updated: Last update time of the feed
        metadata: Additional metadata about the feed
    """

    title: str = ""
    link: str = ""
    description: str = ""
    language: Optional[str] = None
    articles: List[RSSArticle] = Field(default_factory=list)
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RSSProcessorConfig(BaseModel):
    """Configuration for RSS processor.

    Attributes:
        max_articles: Maximum number of articles to process
        timeout: Timeout for feed fetching in seconds
        user_agent: User agent string for HTTP requests
        verify_ssl: Whether to verify SSL certificates
    """

    max_articles: int = 10
    timeout: int = 30
    user_agent: str = "PepperPy RSS Processor"
    verify_ssl: bool = True


class RSSProcessor(BaseProcessor):
    """Processor for RSS feeds.

    This processor handles fetching and parsing RSS feeds, extracting
    articles, and converting them to structured formats.
    """

    def __init__(self, **config):
        """Initialize the RSS processor.

        Args:
            **config: Configuration parameters for the processor
        """
        self.config = RSSProcessorConfig(**config)

    async def fetch(self, url: str) -> RSSFeed:
        """Fetch and parse an RSS feed.

        Args:
            url: URL of the RSS feed

        Returns:
            Parsed RSS feed

        Raises:
            ValueError: If the URL is invalid
            IOError: If the feed cannot be fetched
        """
        logger.info(f"Fetching RSS feed: {url}")

        try:
            # Import feedparser here to avoid dependency if not used
            import feedparser

            # Run feedparser in executor (blocking operation)
            loop = asyncio.get_event_loop()
            feed_data = await loop.run_in_executor(
                None,
                lambda: feedparser.parse(
                    url,
                    agent=self.config.user_agent,
                ),
            )

            if hasattr(feed_data, "bozo_exception"):
                if feed_data.bozo_exception:
                    logger.warning(f"Feed parsing warning: {feed_data.bozo_exception}")

            # Create feed object
            feed = RSSFeed(
                title=feed_data.feed.get("title", ""),
                link=feed_data.feed.get("link", url),
                description=feed_data.feed.get("description", ""),
                language=feed_data.feed.get("language"),
            )

            # Extract last updated time
            if (
                hasattr(feed_data.feed, "updated_parsed")
                and feed_data.feed.updated_parsed
            ):
                feed.last_updated = datetime.fromtimestamp(
                    time.mktime(feed_data.feed.updated_parsed)
                )

            # Process articles
            articles = []
            for entry in feed_data.entries[: self.config.max_articles]:
                # Convert published date
                published_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published_date = datetime.fromtimestamp(
                            time.mktime(entry.published_parsed)
                        )
                    except Exception as e:
                        logger.warning(f"Error converting date: {e}")

                # Extract categories
                categories = []
                if hasattr(entry, "tags"):
                    categories = [
                        tag.get("term", "") for tag in entry.tags if tag.get("term")
                    ]

                # Extract content
                content = None
                if hasattr(entry, "content"):
                    content = entry.content[0].value if entry.content else None
                elif hasattr(entry, "description"):
                    content = entry.description

                # Extract media
                media = {}
                if hasattr(entry, "media_content"):
                    media["content"] = entry.media_content
                if hasattr(entry, "media_thumbnail"):
                    media["thumbnail"] = entry.media_thumbnail

                # Create article
                article = RSSArticle(
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    summary=entry.get("summary", ""),
                    published=published_date,
                    author=entry.get("author"),
                    categories=categories,
                    content=content,
                    media=media,
                )

                articles.append(article)

            feed.articles = articles
            logger.info(f"Fetched {len(articles)} articles from {url}")

            return feed

        except ImportError:
            logger.error("feedparser library is required for RSS processing")
            raise ImportError(
                "feedparser library is required for RSS processing. "
                "Install it with: pip install feedparser"
            )
        except Exception as e:
            logger.error(f"Error fetching RSS feed: {e}")
            raise IOError(f"Failed to fetch RSS feed: {e}")

    async def process(self, source: Union[str, Path], **kwargs) -> RSSFeed:
        """Process an RSS feed from a URL or file.

        Args:
            source: URL or path to the RSS feed
            **kwargs: Additional processing parameters

        Returns:
            Processed RSS feed

        Raises:
            ValueError: If the source is invalid
            IOError: If the feed cannot be processed
        """
        max_articles = kwargs.get("max_articles", self.config.max_articles)

        # Update config if max_articles is provided
        if max_articles != self.config.max_articles:
            self.config.max_articles = max_articles

        # Process as URL if it starts with http
        if isinstance(source, str) and (
            source.startswith("http://") or source.startswith("https://")
        ):
            return await self.fetch(source)

        # Process as file
        try:
            path = Path(source)
            if not path.exists():
                raise ValueError(f"File not found: {path}")

            # Import feedparser here to avoid dependency if not used
            import feedparser

            # Run feedparser in executor (blocking operation)
            loop = asyncio.get_event_loop()
            feed_data = await loop.run_in_executor(None, lambda: feedparser.parse(path))

            # Create feed object (similar to fetch method)
            # ... (implementation similar to fetch method)

            # For brevity, we'll just call fetch with a file:// URL
            file_url = f"file://{path.absolute()}"
            return await self.fetch(file_url)

        except Exception as e:
            logger.error(f"Error processing RSS feed: {e}")
            raise IOError(f"Failed to process RSS feed: {e}")
