"""Response types module."""

from typing import TypedDict


class ResponseMetadata(TypedDict, total=False):
    """Response metadata dictionary.

    Attributes:
        model: Model used for generation
        provider: Provider name
        usage: Usage statistics
        finish_reason: Reason for completion
    """

    model: str
    provider: str
    usage: dict[str, int]
    finish_reason: str


class AIResponse:
    """Response from an AI provider.

    Attributes:
        content: The response content
        metadata: Additional metadata
    """

    def __init__(self, content: str, metadata: ResponseMetadata | None = None) -> None:
        """Initialize response.

        Args:
            content: Response content
            metadata: Additional metadata
        """
        self.content = content
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, str | ResponseMetadata]:
        """Convert response to dictionary.

        Returns:
            Dictionary representation of the response
        """
        return {
            "content": self.content,
            "metadata": self.metadata,
        }
