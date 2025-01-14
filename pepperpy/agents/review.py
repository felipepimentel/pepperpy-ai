"""Review agent implementation."""

from typing import Any

from ..base.message import MessageHandler
from .types import AgentConfig


class ReviewAgent(MessageHandler):
    """Review agent for code and design reviews."""

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
        """Handle a review message.

        Args:
            system_message: The system message
            user_message: The user message
            conversation_history: Optional conversation history
            metadata: Optional metadata

        Returns:
            The review response
        """
        self._ensure_initialized()

        # Use metadata to determine review type
        review_type = metadata.get("review_type") if metadata else None

        if review_type == "code":
            return f"Code review for: {user_message}"
        elif review_type == "design":
            return f"Design review for: {user_message}"
        elif review_type == "documentation":
            return f"Documentation review for: {user_message}"
        else:
            return f"General review for: {user_message}"

    def _ensure_initialized(self) -> None:
        """Ensure agent is initialized."""
        if not self._initialized:
            raise RuntimeError("Agent not initialized")

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._initialized
