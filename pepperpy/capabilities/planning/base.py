"""Planning capabilities for Pepperpy agents.

This module provides core planning capabilities, including:
- Task planning
- Resource planning
- Action planning
- Goal planning
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Generic, Protocol, TypeVar
from uuid import UUID

from pepperpy.core.types import Context

logger = logging.getLogger(__name__)

# Type variables for generic planning
T = TypeVar("T")  # Input type
S = TypeVar("S")  # State type
A = TypeVar("A")  # Action type


class PlanningType(Enum):
    """Types of planning operations."""

    TASK = auto()
    RESOURCE = auto()
    ACTION = auto()
    GOAL = auto()


@dataclass
class PlanningContext(Context):
    """Context for planning operations.

    Attributes:
        planning_type: Type of planning operation
        constraints: Planning constraints
        preferences: Planning preferences
        metadata: Additional metadata
    """

    planning_type: PlanningType
    constraints: dict[str, Any] = field(default_factory=dict)
    preferences: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanStep(Generic[A]):
    """A single step in a plan.

    Attributes:
        id: Unique identifier for the step
        action: Action to take
        dependencies: IDs of steps this step depends on
        metadata: Additional metadata
    """

    id: UUID
    action: A
    dependencies: list[UUID] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan(Generic[A]):
    """A complete plan consisting of ordered steps.

    Attributes:
        steps: Ordered list of plan steps
        metadata: Additional metadata
    """

    steps: list[PlanStep[A]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult(Generic[A]):
    """Result of executing a plan.

    Attributes:
        success: Whether execution was successful
        completed_steps: Steps that were completed
        failed_step: Step that failed, if any
        error: Error that occurred, if any
        metadata: Additional metadata
    """

    success: bool
    completed_steps: list[PlanStep[A]] = field(default_factory=list)
    failed_step: PlanStep[A] | None = None
    error: Exception | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BasePlanning(Protocol[T, S, A]):
    """Base protocol for planning operations."""

    async def plan(self, input_data: T, state: S) -> Plan[A]:
        """Create a plan from input data and current state.

        Args:
            input_data: Input data to plan from
            state: Current state to plan for

        Returns:
            Generated plan

        Raises:
            PlanningError: If planning fails
        """
        ...

    async def validate(self, plan: Plan[A], state: S) -> bool:
        """Validate a plan against current state.

        Args:
            plan: Plan to validate
            state: State to validate against

        Returns:
            Whether plan is valid

        Raises:
            PlanningError: If validation fails
        """
        ...

    async def execute(self, plan: Plan[A], state: S) -> ExecutionResult[A]:
        """Execute a plan from current state.

        Args:
            plan: Plan to execute
            state: State to execute from

        Returns:
            Result of execution

        Raises:
            PlanningError: If execution fails
        """
        ...

    async def replan(self, plan: Plan[A], state: S) -> Plan[A]:
        """Replan based on current state.

        Args:
            plan: Original plan
            state: Current state

        Returns:
            Updated plan

        Raises:
            PlanningError: If replanning fails
        """
        ...

    async def optimize(self, plan: Plan[A], state: S) -> Plan[A]:
        """Optimize a plan for better performance.

        Args:
            plan: Plan to optimize
            state: State to optimize for

        Returns:
            Optimized plan

        Raises:
            PlanningError: If optimization fails
        """
        ...

    async def merge(self, plans: list[Plan[A]], state: S) -> Plan[A]:
        """Merge multiple plans into a single plan.

        Args:
            plans: Plans to merge
            state: State to merge for

        Returns:
            Merged plan

        Raises:
            PlanningError: If merging fails
        """
        ...
