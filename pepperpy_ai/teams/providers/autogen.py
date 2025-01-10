"""Autogen team provider implementation"""

from collections.abc import Sequence
from typing import Any

from ...ai_types import AIMessage, AIResponse
from ...types import MessageRole
from ..base import BaseTeamProvider
from ..types import AgentRole


class AutogenTeamProvider(BaseTeamProvider):
    """Autogen team provider implementation"""

    async def _setup(self) -> None:
        """Setup provider resources"""
        pass

    async def _teardown(self) -> None:
        """Teardown provider resources"""
        pass

    async def execute_task(self, task: str, **kwargs: Any) -> AIResponse:
        """Execute team task"""
        self._ensure_initialized()
        return AIResponse(
            content=f"Autogen team executing: {task}",
            messages=[AIMessage(role=MessageRole.ASSISTANT, content=task)],
            metadata={"provider": "autogen"},
        )

    async def get_team_members(self) -> Sequence[str]:
        """Get team members"""
        self._ensure_initialized()
        return ["autogen"]

    async def get_team_roles(self) -> dict[str, str]:
        """Get team roles"""
        self._ensure_initialized()
        return {
            "planner": AgentRole.PLANNER.value,
            "executor": AgentRole.EXECUTOR.value,
        }
