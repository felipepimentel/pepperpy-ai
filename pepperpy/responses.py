"""Response types and data classes for AI interactions."""

from dataclasses import dataclass
from typing import Any, Literal, NotRequired, TypedDict

from .base import BaseData


class UsageMetadata(TypedDict):
    """Usage metadata for responses.

    Attributes:
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        total_tokens: Total number of tokens used.
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ResponseMetadata(TypedDict, total=False):
    """Response metadata with optional fields.

    Attributes:
        model: The model used for generation.
        provider: The AI provider used.
        temperature: The temperature setting used.
        max_tokens: Maximum tokens setting used.
        finish_reason: Reason for completion.
        usage: Token usage statistics.
        settings: Additional provider-specific settings.
    """

    model: NotRequired[str]
    provider: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    finish_reason: NotRequired[str]
    usage: NotRequired[UsageMetadata]
    settings: NotRequired[dict[str, Any]]


@dataclass
class ResponseData(BaseData):
    """Response data with metadata support.

    This class represents an AI response with associated metadata
    about the generation process.

    Attributes:
        content: The generated content.
        metadata: Associated metadata about the generation.
    """

    content: str
    metadata: ResponseMetadata

    def __getitem__(self, key: Literal["content", "metadata"]) -> Any:
        """Get item by key.

        Args:
            key: The key to get.

        Returns:
            The value for the key.

        Raises:
            KeyError: If the key doesn't exist.
        """
        if key == "content":
            return self.content
        if key == "metadata":
            return self.metadata
        raise KeyError(key)

    def get(self, key: Literal["content", "metadata"], default: Any = None) -> Any:
        """Get item by key with default value.

        Args:
            key: The key to get.
            default: Default value if key doesn't exist.

        Returns:
            The value for the key or default.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: The key to check.

        Returns:
            Whether the key exists.
        """
        return key in {"content", "metadata"}

    @property
    def model(self) -> str | None:
        """Get the model used for generation.

        Returns:
            The model name or None if not available.
        """
        return self.metadata.get("model")

    @property
    def provider(self) -> str | None:
        """Get the provider used for generation.

        Returns:
            The provider name or None if not available.
        """
        return self.metadata.get("provider")

    @property
    def usage(self) -> UsageMetadata | None:
        """Get token usage statistics.

        Returns:
            Token usage statistics or None if not available.
        """
        return self.metadata.get("usage")

    @property
    def total_tokens(self) -> int | None:
        """Get total tokens used.

        Returns:
            Total tokens used or None if not available.
        """
        usage = self.usage
        return usage["total_tokens"] if usage else None

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            The response content.
        """
        return self.content
