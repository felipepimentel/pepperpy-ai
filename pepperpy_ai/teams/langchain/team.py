"""Langchain team implementation."""

from collections.abc import Sequence
from typing import Any

from ...ai_types import AIMessage, AIResponse
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
        """Execute team task.

        Args:
            task: Task to execute
            **kwargs: Additional arguments

        Returns:
            AI response

        Raises:
            RuntimeError: If team not initialized
        """
        self._ensure_initialized()

        messages = [
            AIMessage(role=MessageRole.USER, content=task),
            AIMessage(
                role=MessageRole.ASSISTANT, content=f"Langchain team executing: {task}"
            ),
        ]
        return AIResponse(
            content=f"Langchain team executing: {task}",
            messages=messages,
            metadata={"provider": "langchain"},
        )

    async def get_team_members(self) -> Sequence[str]:
        """Get team members.

        Returns:
            List of team member names

        Raises:
            RuntimeError: If team not initialized
        """
        self._ensure_initialized()
        return ["researcher", "writer"]

    async def get_team_roles(self) -> dict[str, str]:
        """Get team roles.

        Returns:
            Dictionary mapping member names to roles

        Raises:
            RuntimeError: If team not initialized
        """
        self._ensure_initialized()
        return {
            "researcher": AgentRole.PLANNER.value,
            "writer": AgentRole.ASSISTANT.value,
        }
