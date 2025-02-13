"""Session management for agent and workflow execution.

This module provides classes for tracking and monitoring the execution of
agents and workflows, including progress, thoughts, and intermediate results.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Optional

from structlog import get_logger

logger = get_logger()


class SessionState(Enum):
    """Possible states for a session."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Thought:
    """A thought or reasoning step from an agent."""

    agent: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Step:
    """A step in the execution process."""

    name: str
    description: str
    agent: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None


class Session:
    """Tracks the execution of an agent or workflow.

    The session provides:
    - Current state and progress
    - Thought process and reasoning
    - Intermediate results and artifacts
    - Error handling and recovery
    """

    def __init__(
        self,
        task: str,
        *,
        agent: str | None = None,
        workflow: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a new session."""
        self.task = task
        self.agent = agent
        self.workflow = workflow
        self.metadata = metadata or {}

        self.state = SessionState.CREATED
        self.started_at = datetime.now()
        self.completed_at: datetime | None = None

        self.steps: list[Step] = []
        self.thoughts: list[Thought] = []
        self._current_step: Step | None = None

    @property
    def current_step(self) -> Step | None:
        """Get the current execution step."""
        return self._current_step

    @property
    def progress(self) -> float:
        """Get the progress as a percentage (0-100)."""
        if not self.steps:
            return 0.0
        completed = sum(1 for step in self.steps if step.completed_at)
        return (completed / len(self.steps)) * 100

    def add_thought(
        self,
        agent: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a thought from an agent."""
        thought = Thought(
            agent=agent,
            content=content,
            metadata=metadata or {},
        )
        self.thoughts.append(thought)
        logger.debug("thought_recorded", agent=agent, content=content)

    def start_step(
        self,
        name: str,
        description: str,
        agent: str,
    ) -> None:
        """Start a new execution step."""
        step = Step(
            name=name,
            description=description,
            agent=agent,
            status="running",
            started_at=datetime.now(),
        )
        self.steps.append(step)
        self._current_step = step
        logger.info(
            "step_started",
            step=name,
            description=description,
            agent=agent,
        )

    def complete_step(
        self,
        result: Any | None = None,
    ) -> None:
        """Complete the current step."""
        if self._current_step:
            self._current_step.completed_at = datetime.now()
            self._current_step.status = "completed"
            if result is not None:
                self._current_step.result = result
            logger.info(
                "step_completed",
                step=self._current_step.name,
                result=result,
            )
            self._current_step = None

    def fail_step(self, error: str) -> None:
        """Mark the current step as failed."""
        if self._current_step:
            self._current_step.completed_at = datetime.now()
            self._current_step.status = "failed"
            self._current_step.error = error
            logger.error(
                "step_failed",
                step=self._current_step.name,
                error=error,
            )
            self._current_step = None

    @asynccontextmanager
    async def run(self) -> AsyncIterator[Session]:
        """Run the session and track its execution.

        Example:
            >>> async with session.run() as running:
            ...     print(f"Progress: {running.progress}%")
            ...     print(f"Current step: {running.current_step}")
            ...     for thought in running.thoughts:
            ...         print(f"{thought.agent}: {thought.content}")

        """
        self.state = SessionState.RUNNING
        try:
            yield self
            self.state = SessionState.COMPLETED
            self.completed_at = datetime.now()
        except Exception as e:
            self.state = SessionState.FAILED
            self.completed_at = datetime.now()
            if self._current_step:
                self.fail_step(str(e))
            logger.exception("session_failed", error=str(e))
            raise
        finally:
            logger.info(
                "session_ended",
                state=self.state.value,
                progress=self.progress,
                duration=(self.completed_at - self.started_at).total_seconds()
                if self.completed_at
                else None,
            )
