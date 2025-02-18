"""Tests for RSS content provider."""

from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest

from pepperpy.content.providers.rss import RSSProvider

# Sample RSS feed content
SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <link>https://test.com</link>
    <description>Test feed for unit tests</description>
    <item>
      <title>Test Article 1</title>
      <link>https://test.com/1</link>
      <description>Test content 1</description>
      <pubDate>Thu, 14 Feb 2024 12:00:00 GMT</pubDate>
      <author>Test Author</author>
      <category>tech</category>
    </item>
    <item>
      <title>Test Article 2</title>
      <link>https://test.com/2</link>
      <description>Test content 2</description>
      <pubDate>Thu, 14 Feb 2024 11:00:00 GMT</pubDate>
      <category>science</category>
    </item>
  </channel>
</rss>
"""


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession."""
    with patch("pepperpy.content.providers.rss.aiohttp.ClientSession") as mock:
        # Mock response
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=SAMPLE_FEED)

        # Mock context manager
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock.return_value = mock_session

        yield mock


@pytest.fixture
async def provider(mock_aiohttp_session) -> AsyncGenerator[RSSProvider, None]:
    """Create test provider."""
    async with RSSProvider(
        sources=["https://test.com/feed"], language="pt-BR"
    ) as provider:
        yield provider


@pytest.mark.asyncio
async def test_fetch_basic(provider):
    """Test basic feed fetching."""
    # Fetch articles
    articles = await provider.fetch()

    # Verify results
    assert len(articles) == 2

    # Check first article
    assert articles[0].title == "Test Article 1"
    assert articles[0].content == "Test content 1"
    assert articles[0].source == "Test Feed"
    assert articles[0].metadata["link"] == "https://test.com/1"
    assert articles[0].metadata["author"] == "Test Author"
    assert articles[0].metadata["tags"] == ["tech"]

    # Check second article
    assert articles[1].title == "Test Article 2"
    assert articles[1].content == "Test content 2"
    assert articles[1].metadata["tags"] == ["science"]


@pytest.mark.asyncio
async def test_fetch_with_limit(provider):
    """Test fetching with limit."""
    articles = await provider.fetch(limit=1)
    assert len(articles) == 1
    assert articles[0].title == "Test Article 1"


@pytest.mark.asyncio
async def test_fetch_with_since(provider):
    """Test fetching with time filter."""
    # Set cutoff time between articles
    cutoff = datetime(2024, 2, 14, 11, 30)

    # Fetch articles
    articles = await provider.fetch(since=cutoff)
    assert len(articles) == 1
    assert articles[0].title == "Test Article 1"


@pytest.mark.asyncio
async def test_fetch_with_filters(provider):
    """Test fetching with content filters."""
    # Test language filter
    articles = await provider.fetch(filters={"language": "pt-BR"})
    assert len(articles) == 2

    # Test tag filter
    articles = await provider.fetch(filters={"tags": ["tech"]})
    assert len(articles) == 1
    assert articles[0].title == "Test Article 1"


@pytest.mark.asyncio
async def test_search(provider):
    """Test content search."""
    # Search by title
    articles = await provider.search("Article 1")
    assert len(articles) == 1
    assert articles[0].title == "Test Article 1"

    # Search by content
    articles = await provider.search("content 2")
    assert len(articles) == 1
    assert articles[0].title == "Test Article 2"

    # Search by tag
    articles = await provider.search("tech")
    assert len(articles) == 1
    assert articles[0].title == "Test Article 1"


@pytest.mark.asyncio
async def test_process(provider):
    """Test content processing."""
    # Get an article
    articles = await provider.fetch(limit=1)
    article = articles[0]

    # Process article (no processors implemented yet)
    processed = await provider.process(article)
    assert processed == article
