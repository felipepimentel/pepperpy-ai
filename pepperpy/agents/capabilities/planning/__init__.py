"""Planning capability for agents.

This module provides planning capabilities for agents, allowing them to create,
refine, and execute plans to achieve goals.
"""

from pepperpy.agents.capabilities.planning.providers import (
    BasePlanningProvider,
    PlanningResult,
    PlanStatus,
    PlanStep,
)


class PlanningCapability:
    """Planning capability for agents.

    This capability allows agents to create, refine, and execute plans to achieve goals.
    """

    def __init__(self, provider: BasePlanningProvider):
        """Initialize the planning capability.

        Args:
            provider: The planning provider to use
        """
        self.provider = provider

    def create_plan(self, goal: str, constraints=None):
        """Create a plan to achieve a goal.

        Args:
            goal: The goal to achieve
            constraints: Optional constraints to consider

        Returns:
            A planning result containing the plan
        """
        return self.provider.create_plan(goal, constraints)

    def refine_plan(self, plan_id: str, feedback: str):
        """Refine an existing plan based on feedback.

        Args:
            plan_id: The ID of the plan to refine
            feedback: Feedback to incorporate into the plan

        Returns:
            A planning result containing the refined plan
        """
        return self.provider.refine_plan(plan_id, feedback)

    def evaluate_plan(self, plan_id: str):
        """Evaluate a plan against its goal and constraints.

        Args:
            plan_id: The ID of the plan to evaluate

        Returns:
            Evaluation metrics for the plan
        """
        return self.provider.evaluate_plan(plan_id)


__all__ = [
    "PlanningCapability",
    "BasePlanningProvider",
    "PlanningResult",
    "PlanStatus",
    "PlanStep",
]
