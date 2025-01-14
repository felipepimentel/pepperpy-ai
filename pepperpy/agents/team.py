"""Team agent implementation."""

from typing import Any

from ..base.message import MessageHandler
from .types import AgentConfig


class TeamAgent(MessageHandler):
    """Team agent for coordinating multiple agents."""

    def __init__(self, config: AgentConfig) -> None:
        """Initialize agent."""
        self.config = config
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the agent."""
        if not self._initialized:
            await self._setup()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup agent resources."""
        if self._initialized:
            await self._teardown()
            self._initialized = False

    async def _setup(self) -> None:
        """Setup agent resources."""
        pass

    async def _teardown(self) -> None:
        """Teardown agent resources."""
        pass

    async def handle_message(
        self,
        *,
        system_message: str,
        user_message: str,
        conversation_history: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Handle a team message.

        Args:
            system_message: The system message
            user_message: The user message
            conversation_history: Optional conversation history
            metadata: Optional metadata

        Returns:
            The team response
        """
        self._ensure_initialized()

        # Use metadata to determine team operation type
        operation = metadata.get("operation") if metadata else None

        if operation == "planning":
            return f"Team planning for: {user_message}"
        elif operation == "coordination":
            return f"Team coordination for: {user_message}"
        elif operation == "review":
            return f"Team review for: {user_message}"
        else:
            return f"General team response for: {user_message}"

    def _ensure_initialized(self) -> None:
        """Ensure agent is initialized."""
        if not self._initialized:
            raise RuntimeError("Agent not initialized")

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._initialized
