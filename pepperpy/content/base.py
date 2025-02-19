"""Base interfaces for content capability."""

from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl

from pepperpy.core.base import BaseComponent as Processor
from pepperpy.core.base import BaseProvider as Provider


class ContentError(Exception):
    """Base class for content-related errors."""

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            provider: Optional provider name that caused the error
            source: Optional content source that caused the error
            details: Optional additional details
        """
        super().__init__(message)
        self.provider = provider
        self.source = source
        self.details = details or {}


class ContentMetadata(BaseModel):
    """Metadata for content items."""

    language: str = Field(default="en", description="Content language code")
    category: Optional[str] = Field(default=None, description="Content category")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    url: Optional[HttpUrl] = Field(default=None, description="Source URL")
    author: Optional[str] = Field(default=None, description="Content author")
    summary: Optional[str] = Field(default=None, description="Content summary")
    word_count: Optional[int] = Field(default=None, description="Word count")
    read_time: Optional[int] = Field(
        default=None, description="Estimated read time in minutes"
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ContentItem(BaseModel):
    """Represents a single content item."""

    title: str = Field(description="Content title")
    content: str = Field(description="Main content text")
    source: str = Field(description="Content source identifier")
    published_at: datetime = Field(description="Publication timestamp")
    metadata: ContentMetadata = Field(
        default_factory=ContentMetadata,
        description="Content metadata",
    )


class ContentProvider(Provider):
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

        Raises:
            ContentError: If fetching fails
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

        Raises:
            ContentError: If search fails
        """
        pass


class ContentProcessor(Processor):
    """Base class for content processors."""

    @abstractmethod
    async def process(
        self,
        items: Union[ContentItem, List[ContentItem]],
        **kwargs: Any,
    ) -> Union[ContentItem, List[ContentItem]]:
        """Process content items.

        Args:
            items: Single item or list of items to process
            **kwargs: Additional processor-specific parameters

        Returns:
            Processed item(s)

        Raises:
            ContentError: If processing fails
        """
        pass
