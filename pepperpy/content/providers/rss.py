"""RSS provider for content capability."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import feedparser
from pydantic import BaseModel, Field

from pepperpy.content.base import BaseContentProvider, ContentItem


class RSSConfig(BaseModel):
    """Configuration for RSS provider."""

    sources: List[str] = Field(
        default=["https://news.google.com/rss"], description="List of RSS feed URLs."
    )
    language: str = Field(
        default="pt-BR", description="Language code for content filtering."
    )
    timeout: float = Field(
        default=10.0, description="Timeout for RSS feed requests in seconds."
    )


class RSSProvider(BaseContentProvider):
    """RSS implementation of content provider."""

    def __init__(self, **config: Any):
        """Initialize provider with configuration.

        Args:
            **config: Configuration parameters
        """
        self.config = RSSConfig(**config)
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )

    async def __aenter__(self):
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and cleanup."""
        await self.session.close()

    async def _fetch_feed(self, url: str) -> List[ContentItem]:
        """Fetch and parse a single RSS feed.

        Args:
            url: RSS feed URL

        Returns:
            List of content items from feed
        """
        async with self.session.get(url) as response:
            feed_content = await response.text()

        feed = feedparser.parse(feed_content)
        items = []

        for entry in feed.entries:
            # Parse date
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published:
                published_at = datetime(*published[:6])
            else:
                published_at = datetime.now()

            # Create content item
            items.append(
                ContentItem(
                    title=entry.title,
                    content=entry.get("summary", ""),
                    source=feed.feed.title,
                    published_at=published_at,
                    metadata={
                        "link": entry.link,
                        "author": entry.get("author"),
                        "tags": [tag.term for tag in entry.get("tags", [])],
                    },
                )
            )

        return items

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
        """
        # Fetch all feeds concurrently
        tasks = [self._fetch_feed(url) for url in self.config.sources]
        results = await asyncio.gather(*tasks)

        # Combine and sort items
        items = []
        for feed_items in results:
            items.extend(feed_items)

        # Apply filters
        if since:
            items = [item for item in items if item.published_at >= since]

        if filters:
            # Apply language filter
            if "language" in filters:
                items = [
                    item
                    for item in items
                    if filters["language"] == self.config.language
                ]

            # Apply tag filter
            if "tags" in filters:
                items = [
                    item
                    for item in items
                    if any(
                        tag in item.metadata.get("tags", []) for tag in filters["tags"]
                    )
                ]

        # Sort by date
        items.sort(key=lambda x: x.published_at, reverse=True)

        # Apply limit
        if limit:
            items = items[:limit]

        return items

    async def search(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[ContentItem]:
        """Search for content items matching query.

        Args:
            query: Search query string
            limit: Maximum number of items to return
            filters: Additional filters to apply
            **kwargs: Additional provider-specific parameters

        Returns:
            List of matching content items
        """
        # Fetch recent items
        items = await self.fetch(limit=100, filters=filters)

        # Simple text search
        query = query.lower()
        matches = []

        for item in items:
            if (
                query in item.title.lower()
                or query in item.content.lower()
                or any(query in tag.lower() for tag in item.metadata.get("tags", []))
            ):
                matches.append(item)

        # Sort by relevance (simple exact match count)
        matches.sort(
            key=lambda x: (
                query in x.title.lower(),
                query in x.content.lower(),
                any(query in tag.lower() for tag in x.metadata.get("tags", [])),
                x.published_at,
            ),
            reverse=True,
        )

        # Apply limit
        if limit:
            matches = matches[:limit]

        return matches

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
