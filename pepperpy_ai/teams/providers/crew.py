"""Crew team provider implementation."""

from collections.abc import Sequence
from typing import Any

from ...ai_types import AIMessage, AIResponse
from ...types import MessageRole
from ..base import BaseTeamProvider
from ..types import AgentRole


class CrewTeamProvider(BaseTeamProvider):
    """Crew team provider implementation."""

    async def _setup(self) -> None:
        """Setup provider resources."""
        if self._client and not self._client.is_initialized:
            await self._client.initialize()

    async def _teardown(self) -> None:
        """Teardown provider resources."""
        if self._client and self._client.is_initialized:
            await self._client.cleanup()

    async def execute_task(self, task: str, **kwargs: Any) -> AIResponse:
        """Execute team task."""
        self._ensure_initialized()

        messages = [
            AIMessage(role=MessageRole.USER, content=task),
            AIMessage(
                role=MessageRole.ASSISTANT, content=f"Crew team executing: {task}"
            ),
        ]
        return AIResponse(
            content=f"Crew team executing: {task}",
            messages=messages,
            metadata={"provider": "crew"},
        )

    async def get_team_members(self) -> Sequence[str]:
        """Get team members."""
        self._ensure_initialized()
        return ["planner", "executor", "reviewer"]

    async def get_team_roles(self) -> dict[str, str]:
        """Get team roles."""
        self._ensure_initialized()
        return {
            "planner": AgentRole.PLANNER.value,
            "executor": AgentRole.EXECUTOR.value,
            "reviewer": AgentRole.REVIEWER.value,
        }
