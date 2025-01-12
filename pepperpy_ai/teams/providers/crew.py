"""Crew team provider implementation."""

from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, Sequence

from ...ai_types import Message, MessageRole
from ...exceptions import ProviderError
from ...providers.base import BaseProvider
from ...providers.config import ProviderConfig
from ...responses import AIResponse
from ..base import BaseTeamProvider
from ..types import AgentRole


class CrewTeamProvider(BaseTeamProvider):
    """Crew team provider implementation."""

    def __init__(self, providers: List[BaseProvider[ProviderConfig]]) -> None:
        """Initialize the crew team provider.

        Args:
            providers: List of AI providers.
        """
        self.providers = providers
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the provider is initialized.

        Returns:
            True if initialized, False otherwise.
        """
        return self._initialized

    async def initialize(self) -> None:
        """Initialize all providers."""
        if not self.is_initialized:
            for provider in self.providers:
                await provider.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up all provider resources."""
        if self.is_initialized:
            for provider in self.providers:
                await provider.cleanup()
            self._initialized = False

    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the team."""
        self._ensure_initialized()
        for provider in self.providers:
            async for response in provider.stream(
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield response

    async def execute_task(self, task: str, **kwargs: Any) -> AIResponse:
        """Execute team task."""
        self._ensure_initialized()
        responses = []
        for provider in self.providers:
            messages = [Message(role=MessageRole.USER, content=task)]
            async for response in provider.stream(messages):
                responses.append(response)
        return responses[-1] if responses else AIResponse(content="No response")

    async def get_team_members(self) -> Sequence[str]:
        """Get team members."""
        if not self.is_initialized:
            await self.initialize()
        return ["planner", "executor", "reviewer"]

    async def get_team_roles(self) -> dict[str, str]:
        """Get team roles."""
        if not self.is_initialized:
            await self.initialize()
        return {
            "planner": AgentRole.PLANNER.value,
            "executor": AgentRole.EXECUTOR.value,
            "reviewer": AgentRole.REVIEWER.value,
        }
