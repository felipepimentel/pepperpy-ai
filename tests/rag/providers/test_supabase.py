"""Tests for the Supabase RAG provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from supabase import Client

from pepperpy.rag import Document, Query
from pepperpy.rag.provider import RAGError
from pepperpy.rag.providers.supabase import SupabaseRAGProvider


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    client = MagicMock(spec=Client)
    client.rpc = AsyncMock()
    client.table = MagicMock()
    client.table().insert = AsyncMock()
    client.table().delete = AsyncMock()
    client.table().select = AsyncMock()
    return client


@pytest.fixture
def provider(mock_supabase_client):
    """Create a SupabaseRAGProvider instance with a mock client."""
    with patch(
        "pepperpy.rag.providers.supabase.create_client",
        return_value=mock_supabase_client,
    ):
        provider = SupabaseRAGProvider(
            supabase_url="http://localhost:54321",
            supabase_key="test-key",
        )
        return provider


@pytest.mark.asyncio
async def test_initialize(provider, mock_supabase_client):
    """Test provider initialization."""
    await provider.initialize()

    # Check that the vector extension was created
    mock_supabase_client.rpc.assert_any_call(
        "create_vector_extension",
        {"extension_name": "vector"},
    )

    # Check that the table was created
    mock_supabase_client.rpc.assert_any_call(
        "execute_sql",
        {"query": pytest.approx("CREATE TABLE IF NOT EXISTS documents", abs=1e-10)},
    )


@pytest.mark.asyncio
async def test_add_documents(provider, mock_supabase_client):
    """Test adding documents."""
    await provider.initialize()

    # Create test document
    doc = Document(
        id="test1",
        content="Test content",
        metadata={"source": "test"},
        embeddings=[0.1, 0.2, 0.3],
    )

    # Add document
    await provider.add_documents([doc])

    # Check that document was added
    mock_supabase_client.table().insert.assert_called_once_with(
        {
            "id": "test1",
            "content": "Test content",
            "metadata": {"source": "test"},
            "embedding": [0.1, 0.2, 0.3],
        }
    )


@pytest.mark.asyncio
async def test_search(provider, mock_supabase_client):
    """Test searching documents."""
    await provider.initialize()

    # Create test query
    query = Query(
        id="q1",
        text="test query",
        embeddings=[0.1, 0.2, 0.3],
    )

    # Mock search results
    mock_supabase_client.rpc.return_value.execute.return_value.data = [
        {
            "id": "test1",
            "content": "Test content",
            "metadata": {"source": "test"},
            "similarity": 0.95,
        }
    ]

    # Perform search
    results = await provider.search(query)

    # Check results
    assert len(results.documents) == 1
    assert results.documents[0].id == "test1"
    assert results.documents[0].content == "Test content"
    assert results.scores[0] == 0.95


@pytest.mark.asyncio
async def test_remove_documents(provider, mock_supabase_client):
    """Test removing documents."""
    await provider.initialize()

    # Remove documents
    await provider.remove_documents(["test1", "test2"])

    # Check that documents were removed
    mock_supabase_client.table().delete().in_.assert_called_once_with(
        "id",
        ["test1", "test2"],
    )


@pytest.mark.asyncio
async def test_get_document(provider, mock_supabase_client):
    """Test getting a document."""
    await provider.initialize()

    # Mock document data
    mock_supabase_client.table().select().eq().execute.return_value.data = [
        {
            "id": "test1",
            "content": "Test content",
            "metadata": {"source": "test"},
            "embedding": [0.1, 0.2, 0.3],
        }
    ]

    # Get document
    doc = await provider.get_document("test1")

    # Check document
    assert doc is not None
    assert doc.id == "test1"
    assert doc.content == "Test content"
    assert doc.metadata == {"source": "test"}
    assert doc.embeddings == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_error_handling(provider):
    """Test error handling."""
    with pytest.raises(RAGError):
        # Try to add document without initializing
        await provider.add_documents(
            [
                Document(id="test1", content="Test content"),
            ]
        )
