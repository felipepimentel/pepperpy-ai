"""
PepperPy Agent Results.

Result classes for agent operations.
"""

from typing import Any

from pepperpy.core.results import TextResult


class ConversationResult(TextResult):
    """Result of a conversation interaction."""

    def __init__(
        self,
        content: str,
        messages: list[dict[str, str]],
        model: str,
        usage: dict[str, int],
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize conversation result.

        Args:
            content: Generated content
            messages: Conversation messages
            model: Model used
            usage: Token usage information
            metadata: Additional metadata
        """
        super().__init__(content=content, metadata=metadata or {})
        self.messages = messages
        self.model = model
        self.usage = usage

        # Add to metadata
        self.metadata["model"] = model
        self.metadata["usage"] = usage
        self.metadata["message_count"] = len(messages)

    @property
    def message_count(self) -> int:
        """Get the number of messages.

        Returns:
            Message count
        """
        return len(self.messages)

    def get_message(self, index: int) -> dict[str, str] | None:
        """Get a specific message.

        Args:
            index: Message index

        Returns:
            Message dict or None if out of range
        """
        if 0 <= index < len(self.messages):
            return self.messages[index]
        return None

    def get_latest_user_message(self) -> dict[str, str] | None:
        """Get the most recent user message.

        Returns:
            Latest user message or None if not found
        """
        for msg in reversed(self.messages):
            if msg.get("role") == "user":
                return msg
        return None

    def get_latest_assistant_message(self) -> dict[str, str] | None:
        """Get the most recent assistant message.

        Returns:
            Latest assistant message or None if not found
        """
        for msg in reversed(self.messages):
            if msg.get("role") == "assistant":
                return msg
        return None


class AgentTaskResult(TextResult):
    """Result of an agent task execution."""

    def __init__(
        self,
        content: str,
        task_name: str,
        task_type: str,
        steps: list[dict[str, Any]] | None = None,
        model: str | None = None,
        usage: dict[str, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize agent task result.

        Args:
            content: Generated content
            task_name: Name of the task
            task_type: Type of task
            steps: Execution steps (optional)
            model: Model used (optional)
            usage: Token usage information (optional)
            metadata: Additional metadata
        """
        super().__init__(content=content, metadata=metadata or {})
        self.task_name = task_name
        self.task_type = task_type
        self.steps = steps or []
        self.model = model
        self.usage = usage or {}

        # Add to metadata
        self.metadata["task_name"] = task_name
        self.metadata["task_type"] = task_type
        if model:
            self.metadata["model"] = model
        if usage:
            self.metadata["usage"] = usage
        if steps:
            self.metadata["step_count"] = len(steps)

    @property
    def step_count(self) -> int:
        """Get the number of execution steps.

        Returns:
            Step count
        """
        return len(self.steps)

    def get_step(self, index: int) -> dict[str, Any] | None:
        """Get a specific execution step.

        Args:
            index: Step index

        Returns:
            Step dictionary or None if out of range
        """
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None
