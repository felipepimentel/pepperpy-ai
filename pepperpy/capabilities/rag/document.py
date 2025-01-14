"""Document module."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Document:
    """Document class.

    Attributes:
        content: Document content.
        metadata: Optional document metadata.
    """

    content: str
    metadata: dict[str, Any] | None = None
