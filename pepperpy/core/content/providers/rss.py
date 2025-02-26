"""RSS provider for content capability."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl

from pepperpy.content.base import (
    ContentError,
    ContentItem,
    ContentMetadata,
    ContentProvider,
)


class RSSConfig(BaseModel):
    """Configuration for RSS provider."""

    sources: List[HttpUrl] = Field(description="List of RSS feed URLs")
    language: str = Field(default="en", description="Content language code")
    timeout: float = Field(default=10.0, description="Request timeout in seconds")
    max_items: int = Field(default=100, description="Maximum items per feed")
    user_agent: str = Field(
        default="Pepperpy/1.0 RSS Reader",
        description="User agent string for requests",
    )


class RSSProvider(ContentProvider):
    """RSS implementation of content provider."""

    def __init__(self, **config: Any):
        """Initialize provider with configuration.

        Args:
            **config: Configuration parameters

        Raises:
            ContentError: If configuration is invalid
        """
        try:
            self.config = RSSConfig(**config)
            self.session: Optional[aiohttp.ClientSession] = None
        except Exception as e:
            raise ContentError(
                "Failed to initialize RSS provider",
                provider="rss",
                details={"error": str(e)},
            )

    async def initialize(self) -> None:
        """Initialize the provider.

        Raises:
            ContentError: If initialization fails
        """
        try:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": self.config.user_agent}
            )
        except Exception as e:
            raise ContentError(
                "Failed to initialize RSS session",
                provider="rss",
                details={"error": str(e)},
            )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _fetch_feed(self, url: HttpUrl) -> List[ContentItem]:
        """Fetch and parse a single RSS feed.

        Args:
            url: Feed URL to fetch

        Returns:
            List of content items from the feed

        Raises:
            ContentError: If feed fetching fails
        """
        if not self.session:
            raise ContentError(
                "Provider not initialized",
                provider="rss",
                source=str(url),
            )

        try:
            async with self.session.get(
                str(url), timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status != 200:
                    raise ContentError(
                        f"Failed to fetch feed: HTTP {response.status}",
                        provider="rss",
                        source=str(url),
                    )

                content = await response.text()
                feed = feedparser.parse(content)

                items = []
                for entry in feed.entries[: self.config.max_items]:
                    # Extract text content from HTML
                    soup = BeautifulSoup(
                        entry.get("description", ""), features="html.parser"
                    )
                    text_content = soup.get_text(separator=" ", strip=True)

                    # Create metadata
                    metadata = ContentMetadata(
                        language=self.config.language,
                        category=entry.get("category"),
                        tags=[tag.term for tag in entry.get("tags", [])],
                        url=entry.get("link"),
                        author=entry.get("author"),
                        summary=entry.get("summary"),
                    )

                    # Create content item
                    items.append(
                        ContentItem(
                            title=entry.get("title", "Untitled"),
                            content=text_content,
                            source=urlparse(str(url)).netloc,
                            published_at=datetime(
                                *(
                                    entry.get("published_parsed")
                                    or entry.get("updated_parsed")
                                )
                            ),
                            metadata=metadata,
                        )
                    )

                return items

        except ContentError:
            raise
        except Exception as e:
            raise ContentError(
                "Failed to process feed",
                provider="rss",
                source=str(url),
                details={"error": str(e)},
            )

    async def fetch(
        self,
        *,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[ContentItem]:
        """Fetch content items from RSS feeds.

        Args:
            limit: Maximum number of items to fetch
            since: Only fetch items published after this time
            filters: Additional filters to apply
            **kwargs: Additional provider-specific parameters

        Returns:
            List of content items

        Raises:
            ContentError: If fetching fails
        """
        try:
            # Fetch all feeds concurrently
            tasks = [self._fetch_feed(url) for url in self.config.sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            items = []
            for result in results:
                if isinstance(result, List):
                    items.extend(result)
                elif isinstance(result, Exception):
                    # Log error but continue processing other feeds
                    continue

            # Apply filters
            if since:
                items = [item for item in items if item.published_at >= since]
            if filters:
                if "language" in filters:
                    items = [
                        item
                        for item in items
                        if item.metadata.language == filters["language"]
                    ]
                if "category" in filters:
                    items = [
                        item
                        for item in items
                        if item.metadata.category == filters["category"]
                    ]

            # Sort by publication date (newest first)
            items.sort(key=lambda x: x.published_at, reverse=True)

            # Apply limit
            if limit:
                items = items[:limit]

            return items

        except Exception as e:
            raise ContentError(
                "Failed to fetch content",
                provider="rss",
                details={"error": str(e)},
            )

    async def search(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[ContentItem]:
        """Search for content items matching the query.

        Args:
            query: Search query string
            limit: Maximum number of items to return
            filters: Additional filters to apply
            **kwargs: Additional provider-specific parameters

        Returns:
            List of matching content items

        Raises:
            ContentError: If search fails
        """
        try:
            # Fetch all items first
            items = await self.fetch(filters=filters, **kwargs)

            # Simple text search implementation
            query = query.lower()
            matches = []
            for item in items:
                if (
                    query in item.title.lower()
                    or query in item.content.lower()
                    or query in (item.metadata.summary or "").lower()
                ):
                    matches.append(item)

            # Apply limit
            if limit:
                matches = matches[:limit]

            return matches

        except Exception as e:
            raise ContentError(
                "Failed to search content",
                provider="rss",
                details={"error": str(e), "query": query},
            )

    async def process(
        self,
        item: ContentItem,
        *,
        processors: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ContentItem:
        """Process a content item.

        Args:
            item: Content item to process
            processors: List of processor names to apply
            **kwargs: Additional processor-specific parameters

        Returns:
            Processed content item
        """
        # No processing implemented yet
        return item
