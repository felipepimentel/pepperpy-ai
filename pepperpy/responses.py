"""Response types module."""

from typing import Any, NotRequired, TypedDict


class UsageMetadata(TypedDict):
    """Usage metadata for responses."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ResponseMetadata(TypedDict, total=False):
    """Response metadata."""

    model: NotRequired[str]
    provider: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    finish_reason: NotRequired[str]
    usage: NotRequired[UsageMetadata]
    settings: NotRequired[dict[str, Any]]


class AIResponse(TypedDict):
    """AI response type."""

    content: str
    metadata: ResponseMetadata
