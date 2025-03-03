"""Base chain interface.

This module defines the base interface for agent chains.
It includes:
- Base chain interface
- Chain configuration
- Common chain types
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from pepperpy.agents.base import AgentMessage
from pepperpy.core.errors import PepperpyError


class ChainError(PepperpyError):
    """Raised when a chain operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR008", **(details or {})}
        super().__init__(
            message,
            details=error_details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class ChainConfig(BaseModel):
    """Chain configuration.

    Attributes:
        id: Chain ID
        name: Chain name
        description: Chain description
        parameters: Chain parameters
        metadata: Additional metadata

    """

    id: UUID
    name: str
    description: str = ""
    parameters: dict[str, Any] = {}
    metadata: dict[str, Any] = {}


class ChainStep(BaseModel):
    """Step in a chain execution.

    Attributes:
        step_id: Step ID
        step_type: Type of step
        input: Input messages
        output: Output messages
        metadata: Additional metadata

    """

    step_id: str
    step_type: str
    input: list[AgentMessage]
    output: list[AgentMessage]
    metadata: dict[str, Any] = {}


class ChainResult(BaseModel):
    """Result of a chain execution.

    Attributes:
        chain_id: Chain ID
        steps: List of execution steps
        metadata: Additional metadata

    """

    chain_id: UUID
    steps: list[ChainStep]
    metadata: dict[str, Any] = {}


class Chain:
    """Base class for agent chains.

    This class defines the interface that all chains must implement.
    """

    def __init__(
        self,
        config: ChainConfig,
        **kwargs: Any,
    ) -> None:
        """Initialize chain.

        Args:
            config: Chain configuration
            **kwargs: Additional chain-specific parameters

        """
        self._config = config
        self._steps: list[ChainStep] = []

    @property
    def config(self) -> ChainConfig:
        """Get chain configuration."""
        return self._config

    @property
    def steps(self) -> list[ChainStep]:
        """Get chain steps."""
        return self._steps

    async def execute(
        self,
        messages: list[AgentMessage],
        **kwargs: Any,
    ) -> ChainResult:
        """Execute the chain.

        Args:
            messages: Initial messages
            **kwargs: Additional execution parameters

        Returns:
            Chain execution result

        Raises:
            ChainError: If execution fails

        """
        raise NotImplementedError("Chain must implement execute method")
