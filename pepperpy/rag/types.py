"""RAG types module."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Document:
    """Document for RAG."""

    text: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Query:
    """Query for RAG."""

    text: str
    metadata: Optional[Dict[str, Any]] = None
