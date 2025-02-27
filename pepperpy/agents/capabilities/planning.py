"""Module for agent planning capabilities."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class PlanStatus(Enum):
    """Status of a plan or plan step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class PlanStep:
    """Represents a single step in a plan."""

    id: str
    description: str
    dependencies: List[str]  # IDs of steps that must complete before this one
    status: PlanStatus = PlanStatus.PENDING
    result: Optional[Any] = None
    metadata: Optional[dict] = None


@dataclass
class Plan:
    """Represents a complete plan with multiple steps."""

    id: str
    goal: str
    steps: List[PlanStep]
    metadata: Optional[dict] = None

    def get_next_steps(self) -> List[PlanStep]:
        """Get steps that are ready to be executed."""
        ready_steps = []

        for step in self.steps:
            if step.status != PlanStatus.PENDING:
                continue

            # Check if all dependencies are completed
            deps_completed = all(
                any(
                    s.id == dep and s.status == PlanStatus.COMPLETED for s in self.steps
                )
                for dep in step.dependencies
            )

            if deps_completed:
                ready_steps.append(step)

        return ready_steps

    def update_step(self, step_id: str, status: PlanStatus, result: Any = None):
        """Update the status and result of a plan step."""
        for step in self.steps:
            if step.id == step_id:
                step.status = status
                if result is not None:
                    step.result = result
                break

    def is_completed(self) -> bool:
        """Check if the entire plan is completed."""
        return all(step.status == PlanStatus.COMPLETED for step in self.steps)

    def is_failed(self) -> bool:
        """Check if any step has failed."""
        return any(step.status == PlanStatus.FAILED for step in self.steps)


class Planner:
    """Base class for plan generation and management."""

    async def create_plan(
        self, goal: str, context: Optional[Dict[str, Any]] = None
    ) -> Plan:
        """Generate a plan to achieve the specified goal."""
        raise NotImplementedError

    async def refine_plan(self, plan: Plan, feedback: Dict[str, Any]) -> Plan:
        """Refine an existing plan based on feedback or new information."""
        raise NotImplementedError

    async def adapt_plan(self, plan: Plan, new_goal: str) -> Plan:
        """Adapt an existing plan to a new or modified goal."""
        raise NotImplementedError


class PlanExecutor:
    """Base class for plan execution and monitoring."""

    async def execute_step(
        self, step: PlanStep, context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a single plan step."""
        raise NotImplementedError

    async def execute_plan(
        self, plan: Plan, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an entire plan."""
        while not plan.is_completed() and not plan.is_failed():
            next_steps = plan.get_next_steps()

            for step in next_steps:
                try:
                    step.status = PlanStatus.IN_PROGRESS
                    result = await self.execute_step(step, context)
                    plan.update_step(step.id, PlanStatus.COMPLETED, result)
                except Exception as e:
                    plan.update_step(step.id, PlanStatus.FAILED, str(e))
                    raise

        return {step.id: step.result for step in plan.steps}


class PlanManager:
    """High-level interface for plan management and execution."""

    def __init__(self, planner: Planner, executor: PlanExecutor):
        self.planner = planner
        self.executor = executor

    async def plan_and_execute(
        self, goal: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create and execute a plan for the given goal."""
        plan = await self.planner.create_plan(goal, context)
        return await self.executor.execute_plan(plan, context)

    async def replan_and_continue(
        self, plan: Plan, feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Refine a plan based on feedback and continue execution."""
        refined_plan = await self.planner.refine_plan(plan, feedback)
        return await self.executor.execute_plan(refined_plan)
