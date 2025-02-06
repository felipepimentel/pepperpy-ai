"""Type definitions for memory system."""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, validator

# Type variables for generic parameters
K = TypeVar("K", str, UUID)
V = TypeVar("V", bound=dict[str, Any])


class MemoryType(str, Enum):
    """Types of memory storage."""

    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"


class MemoryScope(str, Enum):
    """Scope of memory storage."""

    SESSION = "session"
    AGENT = "agent"
    GLOBAL = "global"


class MemoryEntry(BaseModel, Generic[V]):
    """Memory entry model."""

    key: str = Field(..., description="Memory key")
    value: V = Field(..., description="Memory value")
    type: str = Field(default=MemoryType.SHORT_TERM, description="Memory type")
    scope: str = Field(default=MemoryScope.SESSION, description="Memory scope")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata"
    )
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp"
    )
    expires_at: datetime | None = Field(
        default=None, description="Expiration timestamp"
    )
    indices: set[str] | None = Field(default=None, description="Search indices")


class MemoryIndex(str, Enum):
    """Types of memory indices."""

    SEMANTIC = "semantic"  # Semantic similarity search
    TEMPORAL = "temporal"  # Time-based search
    SPATIAL = "spatial"  # Location-based search
    CAUSAL = "causal"  # Cause-effect relationships
    CONTEXTUAL = "contextual"  # Context-based search


class MemoryQuery(BaseModel):
    """Memory query parameters.

    Attributes:
        query: Search query
        index_type: Type of index to use
        filters: Query filters
        limit: Maximum results
        offset: Result offset
        min_score: Minimum similarity score
        key: Single key to retrieve
        keys: Multiple keys to retrieve
        metadata: Metadata filters
        order_by: Field to order by
        order: Order direction (ASC/DESC)
    """

    query: str = Field(..., min_length=1)
    index_type: MemoryIndex = Field(default=MemoryIndex.SEMANTIC)
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1)
    offset: int = Field(default=0, ge=0)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    key: str | None = Field(default=None)
    keys: list[str] | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
    order_by: str | None = Field(default=None)
    order: str | None = Field(default=None)

    @validator("query")
    def validate_query(self, v: str) -> str:
        """Validate search query."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    @validator("filters")
    def validate_filters(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure filters are immutable."""
        return dict(v)

    @validator("metadata")
    def validate_metadata(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure metadata is immutable."""
        return dict(v)

    @validator("order")
    def validate_order(self, v: str | None) -> str | None:
        """Validate order direction."""
        if v is not None and v.upper() not in ["ASC", "DESC"]:
            raise ValueError("Order must be ASC or DESC")
        return v.upper() if v else None


class MemoryResult(BaseModel, Generic[V]):
    """Memory query result."""

    key: str = Field(..., description="Memory key")
    entry: V = Field(..., description="Memory entry value")
    similarity: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Similarity score"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Result metadata"
    )
