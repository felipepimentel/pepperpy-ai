"""Provider types module."""

from typing import TypedDict


class ProviderKwargs(TypedDict, total=False):
    """Provider keyword arguments."""

    temperature: float | None
    max_tokens: int | None
    top_p: float | None
    frequency_penalty: float | None
    presence_penalty: float | None
    timeout: float | None
    model: str | None


ProviderValue = str | int | float | bool | None
