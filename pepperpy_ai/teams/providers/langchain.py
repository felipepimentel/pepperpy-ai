"""Langchain team provider implementation"""

from collections.abc import Sequence
from typing import Any

from ...ai_types import AIMessage, AIResponse
from ...types import MessageRole
from ..base import BaseTeamProvider
from ..types import AgentRole


class LangchainTeamProvider(BaseTeamProvider):
    """Langchain team provider implementation"""

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
            content=f"Langchain team executing: {task}",
            messages=[AIMessage(role=MessageRole.ASSISTANT, content=task)],
            metadata={"provider": "langchain"},
        )

    async def get_team_members(self) -> Sequence[str]:
        """Get team members"""
        self._ensure_initialized()
        return ["langchain"]

    async def get_team_roles(self) -> dict[str, str]:
        """Get team roles"""
        self._ensure_initialized()
        return {
            "langchain": AgentRole.ASSISTANT.value,
        }
