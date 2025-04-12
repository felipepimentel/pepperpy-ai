"""
Orchestrator Topology.

Implements a centrally-controlled agent topology where a single orchestrator
coordinates the execution of multiple agents in a workflow.
"""

from collections.abc import Sequence
from typing import Any

from pepperpy.agent.base import Message
from pepperpy.core.logging import get_logger

from .base import AgentTopologyProvider, TopologyError

logger = get_logger(__name__)


class OrchestratorTopology(AgentTopologyProvider):
    """Orchestrator topology implementation.

    This topology follows a conductor pattern where a central orchestrator
    manages the workflow, delegating tasks to specialized agents and
    coordinating their interactions.

    Example workflow:
        1. Orchestrator analyzes the task
        2. Orchestrator selects appropriate agents
        3. Orchestrator delegates subtasks to agents
        4. Orchestrator coordinates agent interactions
        5. Orchestrator aggregates results

    Configuration:
        orchestrator_prompt: Template for orchestrator system prompt
        orchestrator_llm: LLM configuration for orchestrator
        agents: Dict of agent configurations by ID
        max_iterations: Maximum number of orchestration iterations
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize orchestrator topology.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.orchestrator_prompt = self.config.get(
            "orchestrator_prompt",
            """You are an orchestrator AI that coordinates a team of specialized agents.
            Your job is to analyze tasks, select appropriate agents, and coordinate their work.
            Available agents: {agent_descriptions}
            
            Task coordination process:
            1. Analyze the input task
            2. Select appropriate agents
            3. Break down the task into subtasks for each agent
            4. Process agent responses
            5. Either request additional agent actions or produce a final result
            
            Respond with a structured plan including:
            - Task analysis
            - Agents selected with rationale
            - Subtasks assigned to each agent
            """,
        )
        self.max_iterations = self.config.get("max_iterations", 10)
        self.orchestrator_llm_config = self.config.get("orchestrator_llm", {})
        self.orchestrator_llm: Any | None = None
        self.conversation_history: list[Message] = []

    async def initialize(self) -> None:
        """Initialize topology resources."""
        if self.initialized:
            return

        try:
            # Initialize the orchestrator LLM
            try:
                # Try to import the LLM provider creator
                from pepperpy.llm import create_provider

                self.orchestrator_llm = create_provider(**self.orchestrator_llm_config)
            except ImportError:
                # Fallback - direct instantiation
                provider_type = self.orchestrator_llm_config.get(
                    "provider_type", "openai"
                )
                if provider_type == "openai":
                    from pepperpy.llm.openai import OpenAIProvider

                    self.orchestrator_llm = OpenAIProvider(self.orchestrator_llm_config)
                else:
                    logger.warning(f"Unsupported LLM provider type: {provider_type}")
                    self.orchestrator_llm = None

            # Initialize LLM if available
            if self.orchestrator_llm and hasattr(self.orchestrator_llm, "initialize"):
                await self.orchestrator_llm.initialize()

            # Create and initialize configured agents
            for agent_id, agent_config in self.agent_configs.items():
                from pepperpy.agent import create_agent

                agent = create_agent(**agent_config)
                await self.add_agent(agent_id, agent)

            self.initialized = True
            logger.info(
                f"Initialized orchestrator topology with {len(self.agents)} agents"
            )
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator topology: {e}")
            await self.cleanup()
            raise TopologyError(f"Initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.orchestrator_llm and hasattr(self.orchestrator_llm, "cleanup"):
            try:
                await self.orchestrator_llm.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up orchestrator LLM: {e}")
            self.orchestrator_llm = None

        await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the orchestrator topology with input data.

        Args:
            input_data: Input containing task details

        Returns:
            Execution results
        """
        if not self.initialized:
            await self.initialize()

        if not self.orchestrator_llm:
            raise TopologyError("Orchestrator LLM not initialized")

        # Reset conversation for this execution
        self.conversation_history = []

        # Extract input task
        task = input_data.get("task", "")
        if not task:
            raise TopologyError("No task provided in input data")

        # Prepare system prompt with agent descriptions
        agent_descriptions = await self._get_agent_descriptions()
        system_prompt = self.orchestrator_prompt.format(
            agent_descriptions=agent_descriptions
        )

        # Start conversation with system prompt
        self.conversation_history.append(Message(role="system", content=system_prompt))
        self.conversation_history.append(Message(role="user", content=task))

        # Execute orchestration iterations
        iteration = 0
        final_result = {}

        while iteration < self.max_iterations:
            iteration += 1
            logger.debug(f"Orchestration iteration {iteration}")

            # Get orchestrator response
            try:
                messages = []
                for msg in self.conversation_history:
                    if hasattr(msg, "to_dict"):
                        messages.append(msg.to_dict())
                    else:
                        # Fallback if to_dict not available
                        messages.append({
                            "role": getattr(msg, "role", "user"),
                            "content": getattr(msg, "content", str(msg)),
                        })

                # Handle different LLM provider interfaces
                orchestrator_response = None
                if hasattr(self.orchestrator_llm, "generate"):
                    orchestrator_response = await self.orchestrator_llm.generate(
                        messages=messages
                    )
                    response_text = orchestrator_response.generations[0].text
                elif hasattr(self.orchestrator_llm, "complete"):
                    orchestrator_response = await self.orchestrator_llm.complete(
                        messages
                    )
                    response_text = orchestrator_response
                else:
                    # Last resort: try calling directly
                    orchestrator_response = await self.orchestrator_llm(messages)
                    if isinstance(orchestrator_response, str):
                        response_text = orchestrator_response
                    else:
                        response_text = str(orchestrator_response)
            except Exception as e:
                logger.error(f"Error getting response from orchestrator LLM: {e}")
                response_text = f"Error: {e}"

            self.conversation_history.append(
                Message(role="assistant", content=response_text)
            )

            # Parse orchestrator response
            action_plan = self._parse_orchestrator_response(response_text)

            # Check for completion
            if action_plan.get("status") == "complete":
                final_result = {"result": action_plan.get("result", {})}
                break

            # Execute agent actions
            agent_results = await self._execute_agent_actions(action_plan)

            # Add agent results to conversation
            agent_results_text = self._format_agent_results(agent_results)
            self.conversation_history.append(
                Message(role="user", content=agent_results_text)
            )

        # Return final result or timeout
        if not final_result:
            final_result = {
                "status": "timeout",
                "message": f"Reached maximum iterations ({self.max_iterations})",
            }

        return final_result

    async def _get_agent_descriptions(self) -> str:
        """Get formatted descriptions of available agents.

        Returns:
            Formatted string with agent descriptions
        """
        descriptions = []
        for agent_id, agent in self.agents.items():
            capabilities = "Unknown capabilities"
            try:
                # Try to get agent capabilities if available
                if hasattr(agent, "get_capabilities") and callable(
                    agent.get_capabilities
                ):
                    try:
                        caps = await agent.get_capabilities()
                        if caps:
                            capabilities = ", ".join(caps)
                    except Exception as e:
                        logger.error(
                            f"Error getting capabilities from agent {agent_id}: {e}"
                        )
            except Exception:
                pass

            descriptions.append(f"- {agent_id}: {capabilities}")

        return "\n".join(descriptions) if descriptions else "No agents available."

    def _parse_orchestrator_response(self, response: str) -> dict[str, Any]:
        """Parse the orchestrator response to extract agent actions.

        Args:
            response: Orchestrator response text

        Returns:
            Action plan with agent tasks
        """
        # Simple parsing logic - in production this would be more robust
        action_plan = {"agent_actions": [], "status": "in_progress"}

        # Check for completion
        if "FINAL RESULT" in response or "TASK COMPLETE" in response:
            action_plan["status"] = "complete"
            action_plan["result"] = response
            return action_plan

        # Extract agent actions
        lines = response.split("\n")
        current_agent = None
        current_action = ""

        for line in lines:
            line = line.strip()

            # Check for agent assignment
            if line.startswith("Agent:") or line.startswith("AGENT:"):
                # Save previous agent action if exists
                if current_agent and current_action:
                    action_plan["agent_actions"].append({
                        "agent_id": current_agent,
                        "action": current_action.strip(),
                    })

                # Extract new agent
                current_agent = line.split(":", 1)[1].strip()
                current_action = ""
            elif current_agent and line:
                # Add to current action
                current_action += line + "\n"

        # Add final agent action if exists
        if current_agent and current_action:
            action_plan["agent_actions"].append({
                "agent_id": current_agent,
                "action": current_action.strip(),
            })

        return action_plan

    async def _execute_agent_actions(
        self, action_plan: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Execute actions for each agent in the plan.

        Args:
            action_plan: Plan with agent actions

        Returns:
            Results from each agent
        """
        results = []

        for action in action_plan.get("agent_actions", []):
            agent_id = action.get("agent_id")
            action_text = action.get("action", "")

            if not agent_id or not action_text or agent_id not in self.agents:
                results.append({
                    "agent_id": agent_id or "unknown",
                    "status": "error",
                    "error": f"Invalid agent or action: {agent_id}",
                })
                continue

            try:
                # Execute the agent action
                agent = self.agents[agent_id]
                result = await agent.process_message(action_text)

                results.append({
                    "agent_id": agent_id,
                    "status": "success",
                    "result": result,
                })
            except Exception as e:
                logger.error(f"Error executing agent {agent_id}: {e}")
                results.append({
                    "agent_id": agent_id,
                    "status": "error",
                    "error": str(e),
                })

        return results

    def _format_agent_results(self, results: Sequence[dict[str, Any]]) -> str:
        """Format agent results for orchestrator consumption.

        Args:
            results: List of agent execution results

        Returns:
            Formatted results string
        """
        formatted = ["AGENT RESULTS:"]

        for result in results:
            agent_id = result.get("agent_id", "unknown")
            status = result.get("status", "unknown")

            if status == "success":
                content = result.get("result", "No result")
                formatted.append(f"[{agent_id}] SUCCESS:\n{content}")
            else:
                error = result.get("error", "Unknown error")
                formatted.append(f"[{agent_id}] ERROR: {error}")

        return "\n\n".join(formatted)
