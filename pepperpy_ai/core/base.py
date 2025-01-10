"""Base classes for pepperpy-ai."""

from typing import Protocol

from pepperpy_ai.client import AIClient
from pepperpy_ai.config import AgentConfig


class BaseAgent(Protocol):
    """Base agent protocol."""

    _client: AIClient
    _initialized: bool
    config: AgentConfig

    def __init__(self, client: AIClient, config: AgentConfig) -> None:
        """Initialize agent."""
        ...

    def _ensure_initialized(self) -> None:
        """Ensure agent is initialized."""
        ...
