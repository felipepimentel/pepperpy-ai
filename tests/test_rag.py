"""Test RAG module."""

import pytest

from pepperpy.utils.dependencies import check_dependency


def test_rag_imports() -> None:
    """Test RAG imports."""
    if not check_dependency("sentence_transformers"):
        pytest.skip("sentence-transformers not installed")

    from pepperpy.capabilities.rag.base import RAGCapability

    assert RAGCapability is not None
