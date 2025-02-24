"""Tests for the unified search and retrieval system."""

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import pytest

from pepperpy.core.memory.unified import MemoryEntry, MemoryStore
from pepperpy.core.search.unified import (
    BaseSearchProvider,
    MemorySearchProvider,
    SearchError,
    SearchManager,
    SearchQuery,
    SearchResult,
)


def test_search_result():
    """Test search result creation and conversion."""
    result = SearchResult(
        id="test",
        score=0.8,
        data="test data",
        metadata={"type": "test"},
        timestamp=datetime.now(),
    )

    assert result.id == "test"
    assert result.score == 0.8
    assert result.data == "test data"
    assert result.metadata == {"type": "test"}

    # Test dictionary conversion
    result_dict = result.to_dict()
    assert result_dict["id"] == "test"
    assert result_dict["score"] == 0.8
    assert result_dict["data"] == "test data"
    assert result_dict["metadata"] == {"type": "test"}
    assert "timestamp" in result_dict


def test_search_query():
    """Test search query building."""
    query = SearchQuery("test query")

    # Test defaults
    assert query.query == "test query"
    assert query.filters == {}
    assert query.sort == []
    assert query.limit is None
    assert query.offset is None

    # Test builder methods
    query.add_filter("type", "test")
    query.add_sort("score")
    query.set_limit(10)
    query.set_offset(5)

    assert query.filters == {"type": "test"}
    assert query.sort == ["score"]
    assert query.limit == 10
    assert query.offset == 5


class MockSearchProvider(BaseSearchProvider[str]):
    """Mock search provider for testing."""

    def __init__(self):
        """Initialize the mock provider."""
        super().__init__()
        self._data: dict[str, str] = {}

    async def search(self, query: SearchQuery) -> AsyncIterator[SearchResult[str]]:
        """Mock search implementation."""
        for id, value in self._data.items():
            if query.query in value:
                yield SearchResult(id=id, score=1.0, data=value)

    async def get(self, id: str) -> str | None:
        """Mock get implementation."""
        return self._data.get(id)

    def add_item(self, id: str, value: str) -> None:
        """Add test item."""
        self._data[id] = value


class TestBaseSearchProvider:
    """Tests for the base search provider."""

    @pytest.fixture
    def provider(self) -> MockSearchProvider:
        """Fixture providing a mock provider."""
        return MockSearchProvider()

    @pytest.mark.asyncio
    async def test_exists(self, provider):
        """Test exists check."""
        provider.add_item("test", "test value")

        assert await provider.exists("test")
        assert not await provider.exists("nonexistent")


class TestMemorySearchProvider:
    """Tests for the memory search provider."""

    class TestMemoryStore(MemoryStore[str]):
        """Test memory store implementation."""

        def __init__(self):
            """Initialize the test store."""
            self._entries: dict[str, MemoryEntry[str]] = {}

        async def get(self, key: str) -> MemoryEntry[str] | None:
            """Get entry by key."""
            return self._entries.get(key)

        async def set(
            self, key: str, value: str, metadata: dict[str, Any] | None = None
        ) -> None:
            """Set entry value."""
            self._entries[key] = MemoryEntry(key=key, value=value, metadata=metadata)

        async def scan(self, pattern: str | None = None) -> AsyncIterator[str]:
            """Scan keys."""
            for key in self._entries:
                if not pattern or pattern in key:
                    yield key

    @pytest.fixture
    def store(self) -> TestMemoryStore:
        """Fixture providing a test memory store."""
        return TestMemoryStore()

    @pytest.fixture
    def provider(self, store) -> MemorySearchProvider[str]:
        """Fixture providing a memory search provider."""
        return MemorySearchProvider(store)

    @pytest.mark.asyncio
    async def test_search(self, store, provider):
        """Test memory store search."""
        # Add test data
        await store.set("test1", "test value 1", metadata={"type": "test"})
        await store.set("test2", "test value 2", metadata={"type": "test"})
        await store.set("other", "other value", metadata={"type": "other"})

        # Search with pattern
        query = SearchQuery("test")
        results = [result async for result in provider.search(query)]
        assert len(results) == 2
        assert all(result.data.startswith("test value") for result in results)

        # Search with filter
        query = SearchQuery("test", filters={"type": "test"})
        results = [result async for result in provider.search(query)]
        assert len(results) == 2
        assert all(result.metadata["type"] == "test" for result in results)

    @pytest.mark.asyncio
    async def test_get(self, store, provider):
        """Test memory store get."""
        await store.set("test", "test value")

        value = await provider.get("test")
        assert value == "test value"

        value = await provider.get("nonexistent")
        assert value is None


class TestSearchManager:
    """Tests for the search manager."""

    @pytest.fixture
    def manager(self) -> SearchManager[str]:
        """Fixture providing a search manager."""
        return SearchManager()

    @pytest.fixture
    def provider1(self) -> MockSearchProvider:
        """Fixture providing the first test provider."""
        provider = MockSearchProvider()
        provider.add_item("test1", "test value 1")
        provider.add_item("test2", "test value 2")
        return provider

    @pytest.fixture
    def provider2(self) -> MockSearchProvider:
        """Fixture providing the second test provider."""
        provider = MockSearchProvider()
        provider.add_item("test3", "test value 3")
        provider.add_item("other", "other value")
        return provider

    def test_register_provider(self, manager, provider1, provider2):
        """Test provider registration."""
        manager.register_provider("provider1", provider1)
        manager.register_provider("provider2", provider2)

        assert "provider1" in manager._providers
        assert "provider2" in manager._providers

    @pytest.mark.asyncio
    async def test_search_with_provider(self, manager, provider1):
        """Test search with specific provider."""
        manager.register_provider("provider1", provider1)

        results = [
            result async for result in manager.search("test", provider="provider1")
        ]
        assert len(results) == 2
        assert all(result.data.startswith("test value") for result in results)

    @pytest.mark.asyncio
    async def test_search_all_providers(self, manager, provider1, provider2):
        """Test search across all providers."""
        manager.register_provider("provider1", provider1)
        manager.register_provider("provider2", provider2)

        results = [result async for result in manager.search("test")]
        assert len(results) == 3
        assert all(result.data.startswith("test value") for result in results)

    @pytest.mark.asyncio
    async def test_search_with_limit_offset(self, manager, provider1, provider2):
        """Test search with limit and offset."""
        manager.register_provider("provider1", provider1)
        manager.register_provider("provider2", provider2)

        query = SearchQuery("test", limit=2, offset=1)
        results = [result async for result in manager.search(query)]
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_with_provider(self, manager, provider1):
        """Test get with specific provider."""
        manager.register_provider("provider1", provider1)

        value = await manager.get("test1", provider="provider1")
        assert value == "test value 1"

        value = await manager.get("nonexistent", provider="provider1")
        assert value is None

    @pytest.mark.asyncio
    async def test_get_all_providers(self, manager, provider1, provider2):
        """Test get across all providers."""
        manager.register_provider("provider1", provider1)
        manager.register_provider("provider2", provider2)

        value = await manager.get("test1")
        assert value == "test value 1"

        value = await manager.get("test3")
        assert value == "test value 3"

        value = await manager.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_provider_not_found(self, manager):
        """Test error handling for unknown provider."""
        with pytest.raises(SearchError) as exc:
            async for _ in manager.search("test", provider="unknown"):
                pass
        assert exc.value.code == "SEARCH001"

        with pytest.raises(SearchError) as exc:
            await manager.get("test", provider="unknown")
        assert exc.value.code == "SEARCH001"
