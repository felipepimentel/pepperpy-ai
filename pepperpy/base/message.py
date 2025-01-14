"""Base message handling for AI components."""

from typing import Any, Protocol


class MessageHandler(Protocol):
    """Protocol for message handling."""

    async def handle_message(
        self,
        *,  # Force keyword arguments
        system_message: str,
        user_message: str,
        conversation_history: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Handle a message.

        Args:
            system_message: The system message
            user_message: The user message
            conversation_history: Optional conversation history
            metadata: Optional metadata

        Returns:
            The response message
        """
        ...
