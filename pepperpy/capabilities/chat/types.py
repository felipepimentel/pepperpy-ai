"""Chat capability types module."""

from typing import NotRequired, TypedDict


class ChatKwargs(TypedDict, total=False):
    """Chat capability keyword arguments."""

    model: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]
