"""Response types module."""

from typing import Any, NotRequired, TypedDict


class ResponseMetadata(TypedDict, total=False):
    """Response metadata."""

    model: NotRequired[str]
    provider: str
    usage: NotRequired[dict[str, Any]]
    finish_reason: NotRequired[str | None]


class AIResponse:
    """AI response."""

    def __init__(self, content: str, metadata: ResponseMetadata) -> None:
        """Initialize response.

        Args:
            content: Response content
            metadata: Response metadata
        """
        self.content = content
        self.metadata = metadata
