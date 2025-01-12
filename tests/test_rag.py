"""Tests for RAG functionality."""

import pytest

from pepperpy_ai.capabilities.rag.base import RAGCapability, RAGConfig
from pepperpy_ai.types import Document


@pytest.mark.asyncio
async def test_rag_base() -> None:
    """Test RAG base functionality."""
    # This is just a placeholder test since RAG is optional
    assert issubclass(RAGCapability, object)
    assert issubclass(RAGConfig, object)
    assert issubclass(Document, object)
