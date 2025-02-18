"""Base interfaces for content capability."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class ContentItem:
    """Represents a single content item."""

    def __init__(
        self,
        title: str,
        content: str,
        source: str,
        published_at: datetime,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.title = title
        self.content = content
        self.source = source
        self.published_at = published_at
        self.metadata = metadata or {}


class BaseContentProvider(ABC):
    """Base class for content providers."""

    @abstractmethod
    async def fetch(
        self,
        *,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[ContentItem]:
        """Fetch content items from the source.

        Args:
            limit: Maximum number of items to fetch
            since: Only fetch items published after this time
            filters: Additional filters to apply
            **kwargs: Additional provider-specific parameters

        Returns:
            List of content items
        """
        pass

    @abstractmethod
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
        """
        pass

    @abstractmethod
    async def process(
        self,
        item: ContentItem,
        *,
        processors: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ContentItem:
        """Process a content item through specified processors.

        Args:
            item: Content item to process
            processors: List of processor names to apply
            **kwargs: Additional processor-specific parameters

        Returns:
            Processed content item
        """
        pass
