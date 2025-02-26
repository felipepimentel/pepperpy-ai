"""Type definitions for vector store.

This module defines types used by the vector store implementation.
"""

from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import Field

from pepperpy.memory.base import MemoryEntry


class VectorMemoryEntry(MemoryEntry):
    """Memory entry with vector embedding.

    Attributes:
        id: Unique identifier for the entry
        embedding: Vector embedding of the entry content
    """

    id: UUID = Field(default_factory=uuid4, description="Entry identifier")
    embedding: Optional[List[float]] = Field(
        default=None,
        description="Vector embedding of the entry content",
    )
