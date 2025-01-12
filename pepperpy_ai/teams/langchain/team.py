"""Langchain team implementation."""

from collections.abc import Sequence
from typing import Any

from ...ai_types import Message
from ...responses import AIResponse
from ...types import MessageRole
from ..base import BaseTeam
from ..types import AgentRole


class LangchainTeam(BaseTeam):
    """Langchain team implementation."""

    def __init__(self, client: Any) -> None:
        """Initialize team.

        Args:
            client: AI client instance
        """
        self._client = client
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if team is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize team."""
        if not self._initialized:
            if not self._client.is_initialized:
                await self._client.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup team resources."""
        if self._initialized:
            await self._client.cleanup()
            self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure team is initialized."""
        if not self._initialized:
            raise RuntimeError("Team not initialized")

    async def execute_task(self, task: str, **kwargs: Any) -> AIResponse:
        """Execute team task."""
        self._ensure_initialized()
        return AIResponse(
            content=f"Langchain team executing: {task}",
            model=kwargs.get("model"),
            provider="langchain",
            metadata={"role": "assistant"}
        )

    async def get_team_members(self) -> Sequence[str]:
        """Get team members."""
        self._ensure_initialized()
        return ["langchain"]

    async def get_team_roles(self) -> dict[str, str]:
        """Get team roles."""
        self._ensure_initialized()
        return {
            "langchain": AgentRole.ASSISTANT.value,
        }
