"""Types for RAG storage.

This module defines types used in the RAG storage module.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Document:
    """A document in the RAG system.

    Attributes:
        id: The document ID
        text: The document text
        metadata: Additional metadata for the document
    """

    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Collection:
    """A collection of documents in the RAG system.

    Attributes:
        name: The collection name
        description: The collection description
        metadata: Additional metadata for the collection
    """

    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """A search result in the RAG system.

    Attributes:
        document: The document
        score: The similarity score
        metadata: Additional metadata for the search result
    """

    document: Document
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
