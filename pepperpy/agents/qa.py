"""Quality assurance agent implementation."""

from typing import Any

from ..base.message import MessageHandler
from .types import AgentConfig


class QualityAssuranceAgent(MessageHandler):
    """Quality assurance agent for testing and verification."""

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
        """Handle a QA message.

        Args:
            system_message: The system message
            user_message: The user message
            conversation_history: Optional conversation history
            metadata: Optional metadata

        Returns:
            The QA response
        """
        self._ensure_initialized()

        # Use metadata to determine QA type
        qa_type = metadata.get("qa_type") if metadata else None

        if qa_type == "testing":
            return f"Test analysis for: {user_message}"
        elif qa_type == "verification":
            return f"Verification for: {user_message}"
        elif qa_type == "validation":
            return f"Validation for: {user_message}"
        else:
            return f"General QA for: {user_message}"

    def _ensure_initialized(self) -> None:
        """Ensure agent is initialized."""
        if not self._initialized:
            raise RuntimeError("Agent not initialized")

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._initialized
