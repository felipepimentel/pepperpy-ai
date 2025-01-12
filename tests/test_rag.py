"""Tests for RAG functionality."""

import pytest

from pepperpy_ai.utils import check_dependency


@pytest.mark.skipif(
    not check_dependency("sentence_transformers"),
    reason="sentence_transformers not installed",
)
def test_rag_imports() -> None:
    """Test RAG imports."""
    from pepperpy_ai.capabilities.rag.base import RAGCapability, RAGConfig
    from pepperpy_ai.types import Document

    assert issubclass(RAGCapability, object)
    assert issubclass(RAGConfig, object)
    assert issubclass(Document, object)
