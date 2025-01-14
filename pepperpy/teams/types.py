"""Team types module."""

from typing import Protocol, TypedDict, runtime_checkable


class TeamParams(TypedDict, total=False):
    """Team parameters."""

    model: str | None
    temperature: float | None
    max_tokens: int | None
    top_p: float | None
    frequency_penalty: float | None
    presence_penalty: float | None
    timeout: float | None


@runtime_checkable
class TeamClient(Protocol):
    """Team client interface."""

    @property
    def is_initialized(self) -> bool:
        """Check if client is initialized."""
        ...

    async def initialize(self) -> None:
        """Initialize client."""
        ...

    async def cleanup(self) -> None:
        """Clean up client resources."""
        ...
