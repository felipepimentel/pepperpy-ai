"""ReAct (Reasoning + Acting) framework implementation."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.agents.types import AgentConfig, AgentResponse


@dataclass
class AgentAction:
    """Action to be taken by the agent."""

    name: str
    args: dict[str, Any]
    confidence: float


@dataclass
class ReActStep:
    """Single step in the ReAct process."""

    thought: str
    action: AgentAction | None = None
    observation: str | None = None


class ReActAgent(BaseAgent):
    """ReAct (Reasoning + Acting) agent.

    Implements iterative reasoning and acting by:
    1. Thinking about the current state
    2. Deciding on an action
    3. Observing the result
    4. Repeating until goal is reached
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize ReAct agent.

        Args:
            config: Agent configuration
        """
        super().__init__(config)
        if config.model_kwargs:
            self.max_steps = config.model_kwargs.get("max_steps", 10)
            self.min_confidence = config.model_kwargs.get("min_confidence", 0.7)
        else:
            self.max_steps = 10
            self.min_confidence = 0.7
        self.steps: list[ReActStep] = []

    async def process(
        self, input_data: dict[str, Any], context: dict[str, Any] | None = None
    ) -> AgentResponse:
        """Process input using ReAct reasoning.

        Args:
            input_data: Input data to process
            context: Optional context information

        Returns:
            Agent's response with metadata
        """
        context = context or {}
        self.steps = []

        try:
            message = input_data["message"]

            # Initial thought about the problem
            current_step = ReActStep(
                thought=f"Let's solve this step by step: {message}"
            )
            self.steps.append(current_step)

            # ReAct loop
            while len(self.steps) < self.max_steps:
                # Decide next action
                action = await self._decide_action(message, self.steps, context)
                current_step.action = action

                if not action:
                    # No action needed, we're done
                    break

                # Execute action and observe
                observation = await self._execute_action(action, context)
                current_step.observation = observation

                # Think about result
                current_step = ReActStep(
                    thought=await self._reflect_on_observation(
                        observation, self.steps, context
                    )
                )
                self.steps.append(current_step)

                # Check if we've reached the goal
                if await self._check_goal_reached(self.steps, context):
                    break

            # Generate final response
            response = await self._generate_response(self.steps, context)

            return AgentResponse(
                text=response,
                metadata={
                    "steps": [
                        {
                            "thought": step.thought,
                            "action": (
                                {
                                    "name": step.action.name,
                                    "args": step.action.args,
                                    "confidence": step.action.confidence,
                                }
                                if step.action
                                else None
                            ),
                            "observation": step.observation,
                        }
                        for step in self.steps
                    ],
                    "num_steps": len(self.steps),
                },
            )

        except Exception as e:
            return AgentResponse(
                text=f"Error in ReAct processing: {e!s}",
                metadata={
                    "steps": [
                        {
                            "thought": step.thought,
                            "action": (
                                {
                                    "name": step.action.name,
                                    "args": step.action.args,
                                    "confidence": step.action.confidence,
                                }
                                if step.action
                                else None
                            ),
                            "observation": step.observation,
                        }
                        for step in self.steps
                    ],
                    "error": str(e),
                },
            )

    async def process_stream(
        self, input_data: dict[str, Any], context: dict[str, Any] | None = None
    ) -> AsyncIterator[str]:
        """Process input and stream responses.

        Args:
            input_data: Input data to process
            context: Optional context information

        Returns:
            Async iterator of response chunks
        """
        context = context or {}
        self.steps = []

        try:
            message = input_data["message"]

            # Initial thought
            yield "Starting ReAct process...\n"
            current_step = ReActStep(
                thought=f"Let's solve this step by step: {message}"
            )
            self.steps.append(current_step)
            yield f"Thought: {current_step.thought}\n"

            # ReAct loop
            while len(self.steps) < self.max_steps:
                # Decide next action
                yield "Deciding next action...\n"
                action = await self._decide_action(message, self.steps, context)
                current_step.action = action

                if not action:
                    yield "No further actions needed.\n"
                    break

                yield f"Action: {action.name}\n"

                # Execute action and observe
                yield "Executing action...\n"
                observation = await self._execute_action(action, context)
                current_step.observation = observation
                yield f"Observation: {observation}\n"

                # Think about result
                yield "Reflecting on observation...\n"
                current_step = ReActStep(
                    thought=await self._reflect_on_observation(
                        observation, self.steps, context
                    )
                )
                self.steps.append(current_step)
                yield f"Thought: {current_step.thought}\n"

                # Check if we've reached the goal
                if await self._check_goal_reached(self.steps, context):
                    yield "Goal reached!\n"
                    break

            # Generate final response
            yield "\nGenerating final response...\n"
            response = await self._generate_response(self.steps, context)
            yield f"\nFinal response: {response}"

        except Exception as e:
            yield f"Error in ReAct processing: {e!s}"

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.steps = []

    async def _decide_action(
        self, message: str, steps: list[ReActStep], context: dict[str, Any]
    ) -> AgentAction | None:
        """Decide next action based on current state.

        Args:
            message: Original input message
            steps: Steps taken so far
            context: Current context

        Returns:
            Next action to take, or None if no action needed
        """
        # TODO: Implement more sophisticated action selection
        # For now, use simple heuristics
        if not steps[-1].action:
            # No action taken in current step
            return AgentAction(name="analyze", args={"text": message}, confidence=0.8)
        return None

    async def _execute_action(
        self, action: AgentAction, context: dict[str, Any]
    ) -> str:
        """Execute an action and return observation.

        Args:
            action: Action to execute
            context: Current context

        Returns:
            Observation from action execution
        """
        # TODO: Implement actual action execution
        # For now, return placeholder observations
        if action.name == "analyze":
            return f"Analysis of '{action.args.get('text', '')}' complete"
        return "Action executed successfully"

    async def _reflect_on_observation(
        self, observation: str, steps: list[ReActStep], context: dict[str, Any]
    ) -> str:
        """Reflect on an observation to generate next thought.

        Args:
            observation: Observation to reflect on
            steps: Steps taken so far
            context: Current context

        Returns:
            Next thought
        """
        # TODO: Implement more sophisticated reflection
        # For now, use simple format
        return f"Based on {observation}, let's proceed with next step"

    async def _check_goal_reached(
        self, steps: list[ReActStep], context: dict[str, Any]
    ) -> bool:
        """Check if goal has been reached.

        Args:
            steps: Steps taken so far
            context: Current context

        Returns:
            True if goal reached, False otherwise
        """
        # Simple heuristic based on number of steps and last observation
        if len(steps) >= self.max_steps:
            return True

        # Check if last step indicates completion
        if steps and steps[-1].observation:
            last_obs = steps[-1].observation.lower()
            completion_indicators = ["complete", "finished", "done", "solved"]
            return any(indicator in last_obs for indicator in completion_indicators)

        return False

    async def _generate_response(
        self, steps: list[ReActStep], context: dict[str, Any]
    ) -> str:
        """Generate final response from steps.

        Args:
            steps: Steps taken
            context: Current context

        Returns:
            Final response
        """
        # TODO: Implement more sophisticated response generation
        # For now, use simple format
        response = "Based on the reasoning process:\n\n"
        for i, step in enumerate(steps, 1):
            response += f"{i}. {step.thought}\n"
            if step.action:
                response += f"   Action: {step.action.name}\n"
            if step.observation:
                response += f"   Observation: {step.observation}\n"
        return response
