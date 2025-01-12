"""Autogen team provider implementation"""

from collections.abc import AsyncGenerator, Sequence
from typing import Any, List, Optional

from ...ai_types import Message, MessageRole
from ...responses import AIResponse
from ...types import MessageRole as AIMessageRole
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

    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the provider."""
        self._ensure_initialized()
        yield AIResponse(
            content=f"Autogen team processing messages",
            model=model,
            provider="autogen",
            metadata={"role": "assistant"}
        )

    async def execute_task(self, task: str, **kwargs: Any) -> AIResponse:
        """Execute team task"""
        self._ensure_initialized()
        return AIResponse(
            content=f"Autogen team executing: {task}",
            model=kwargs.get("model"),
            provider="autogen",
            metadata={"role": "assistant"}
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
