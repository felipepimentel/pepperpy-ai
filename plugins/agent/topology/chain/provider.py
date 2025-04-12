"""
Chain Topology Provider.

Implements a sequential agent topology where tasks flow through agents
in a predefined order, like a processing pipeline.
"""

from typing import Any

from pepperpy.agent.topology.base import AgentTopologyProvider, TopologyError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


class ChainTopologyProvider(AgentTopologyProvider):
    """Chain topology provider.

    Implements a sequential approach to agent coordination where agents process
    tasks in a predefined order, much like a processing pipeline or assembly line.

    This topology is suitable for:
    - Sequential processing tasks
    - Gradual refinement of outputs
    - Multi-step transformation workflows
    - Step-by-step reasoning processes

    Configuration:
        chain_direction: Direction of chain (linear or bidirectional)
        max_iterations: Maximum iterations through the chain
        agent_order: Ordered list of agent IDs defining chain sequence
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize chain topology.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.chain_direction = self.config.get("chain_direction", "linear")
        self.max_iterations = self.config.get("max_iterations", 3)
        self.agent_order = self.config.get("agent_order", [])

    async def initialize(self) -> None:
        """Initialize topology resources."""
        if self.initialized:
            return

        try:
            # Create and initialize configured agents
            for agent_id, agent_config in self.agent_configs.items():
                from pepperpy.agent import create_agent

                agent = create_agent(**agent_config)
                await self.add_agent(agent_id, agent)

            # If agent_order not specified, use all agents in key order
            if not self.agent_order:
                self.agent_order = list(self.agents.keys())

            # Validate agent order
            for agent_id in self.agent_order:
                if agent_id not in self.agents:
                    raise TopologyError(
                        f"Agent {agent_id} specified in chain order but not configured"
                    )

            self.initialized = True
            logger.info(f"Initialized chain topology with {len(self.agents)} agents")
        except Exception as e:
            logger.error(f"Failed to initialize chain topology: {e}")
            await self.cleanup()
            raise TopologyError(f"Initialization failed: {e}") from e

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the chain topology with input data.

        Args:
            input_data: Input containing task details

        Returns:
            Execution results
        """
        if not self.initialized:
            await self.initialize()

        # Extract input task
        task = input_data.get("task", "")
        if not task:
            raise TopologyError("No task provided in input data")

        # Validate chain
        if not self.agent_order:
            raise TopologyError("No agents in chain order")

        # Execute chain process
        try:
            if self.chain_direction == "bidirectional":
                return await self._execute_bidirectional_chain(task, input_data)
            else:
                return await self._execute_linear_chain(task, input_data)
        except Exception as e:
            logger.error(f"Error in chain process: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to complete chain process",
            }

    async def _execute_linear_chain(
        self, task: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a linear chain process.

        Args:
            task: Task description
            input_data: Full input data

        Returns:
            Process results
        """
        # Track chain execution
        chain_steps = []
        current_input = task
        final_output = ""

        # Run through iterations
        for iteration in range(self.max_iterations):
            # Process each agent in order
            for agent_idx, agent_id in enumerate(self.agent_order):
                agent = self.agents[agent_id]
                step_num = iteration * len(self.agent_order) + agent_idx + 1

                # Create step prompt with context
                if agent_idx == 0 and iteration == 0:
                    # First agent in first iteration gets original task
                    prompt = (
                        f"You are the first agent in a processing chain.\n\n"
                        f"TASK: {current_input}\n\n"
                        f"Process this task according to your expertise. Your output will be "
                        f"passed to the next agent in the chain."
                    )
                else:
                    # Later agents get context of previous steps
                    prompt = (
                        f"You are agent #{step_num} in a processing chain.\n\n"
                        f"ORIGINAL TASK: {task}\n\n"
                        f"PREVIOUS AGENT OUTPUT: {current_input}\n\n"
                        f"Continue processing based on the previous agent's output."
                    )

                try:
                    # Process with current agent
                    result = await agent.process_message(prompt)

                    # Record step
                    chain_steps.append({
                        "iteration": iteration,
                        "agent_id": agent_id,
                        "input": current_input,
                        "output": result,
                    })

                    # Update for next step
                    current_input = result
                    final_output = result
                except Exception as e:
                    logger.error(f"Error in agent {agent_id}: {e}")
                    chain_steps.append({
                        "iteration": iteration,
                        "agent_id": agent_id,
                        "input": current_input,
                        "error": str(e),
                    })

                    # Skip to completion with error if chain breaks
                    return {
                        "status": "error",
                        "steps": chain_steps,
                        "result": f"Chain broken at agent {agent_id}: {e}",
                        "iterations_completed": iteration,
                    }

        # Return successful completion
        return {
            "status": "complete",
            "steps": chain_steps,
            "result": final_output,
            "iterations_completed": self.max_iterations,
        }

    async def _execute_bidirectional_chain(
        self, task: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a bidirectional chain process.

        Args:
            task: Task description
            input_data: Full input data

        Returns:
            Process results
        """
        # Track chain execution
        chain_steps = []
        current_input = task
        final_output = ""

        # Run through iterations
        for iteration in range(self.max_iterations):
            # Forward pass
            for agent_idx, agent_id in enumerate(self.agent_order):
                agent = self.agents[agent_id]
                step_num = iteration * len(self.agent_order) * 2 + agent_idx + 1

                # Create forward step prompt
                if agent_idx == 0 and iteration == 0:
                    # First agent in first iteration gets original task
                    prompt = (
                        f"You are the first agent in a bidirectional chain.\n\n"
                        f"TASK: {current_input}\n\n"
                        f"Process this task according to your expertise. Your output will be "
                        f"passed forward in the chain."
                    )
                else:
                    # Later agents get context of previous steps
                    prompt = (
                        f"You are agent #{step_num} in the forward pass of a bidirectional chain.\n\n"
                        f"ORIGINAL TASK: {task}\n\n"
                        f"PREVIOUS AGENT OUTPUT: {current_input}\n\n"
                        f"Continue processing based on the previous agent's output."
                    )

                try:
                    # Process with current agent
                    result = await agent.process_message(prompt)

                    # Record step
                    chain_steps.append({
                        "iteration": iteration,
                        "direction": "forward",
                        "agent_id": agent_id,
                        "input": current_input,
                        "output": result,
                    })

                    # Update for next step
                    current_input = result
                    final_output = result
                except Exception as e:
                    logger.error(f"Error in forward pass, agent {agent_id}: {e}")
                    chain_steps.append({
                        "iteration": iteration,
                        "direction": "forward",
                        "agent_id": agent_id,
                        "input": current_input,
                        "error": str(e),
                    })

                    # Skip to completion with error if chain breaks
                    return {
                        "status": "error",
                        "steps": chain_steps,
                        "result": f"Chain broken at forward pass, agent {agent_id}: {e}",
                        "iterations_completed": iteration,
                    }

            # Backward pass (reverse order)
            for agent_idx, agent_id in enumerate(reversed(self.agent_order)):
                agent = self.agents[agent_id]
                step_num = (
                    iteration * len(self.agent_order) * 2
                    + len(self.agent_order)
                    + agent_idx
                    + 1
                )

                # Create backward step prompt
                prompt = (
                    f"You are agent #{step_num} in the backward pass of a bidirectional chain.\n\n"
                    f"ORIGINAL TASK: {task}\n\n"
                    f"CURRENT STATE: {current_input}\n\n"
                    f"Refine and improve the current state based on your expertise. "
                    f"Your output will be passed backward in the chain."
                )

                try:
                    # Process with current agent
                    result = await agent.process_message(prompt)

                    # Record step
                    chain_steps.append({
                        "iteration": iteration,
                        "direction": "backward",
                        "agent_id": agent_id,
                        "input": current_input,
                        "output": result,
                    })

                    # Update for next step
                    current_input = result
                    final_output = result
                except Exception as e:
                    logger.error(f"Error in backward pass, agent {agent_id}: {e}")
                    chain_steps.append({
                        "iteration": iteration,
                        "direction": "backward",
                        "agent_id": agent_id,
                        "input": current_input,
                        "error": str(e),
                    })

                    # Skip to completion with error if chain breaks
                    return {
                        "status": "error",
                        "steps": chain_steps,
                        "result": f"Chain broken at backward pass, agent {agent_id}: {e}",
                        "iterations_completed": iteration,
                    }

        # Return successful completion
        return {
            "status": "complete",
            "steps": chain_steps,
            "result": final_output,
            "iterations_completed": self.max_iterations,
        }

    async def set_agent_order(self, agent_order: list[str]) -> None:
        """Set the order of agents in the chain.

        Args:
            agent_order: Ordered list of agent IDs

        Raises:
            TopologyError: If any agent ID is invalid
        """
        # Validate agent IDs
        for agent_id in agent_order:
            if agent_id not in self.agents:
                raise TopologyError(f"Invalid agent ID '{agent_id}' in chain order")

        self.agent_order = agent_order
        logger.info(f"Updated chain order: {' -> '.join(self.agent_order)}")

    async def get_agent_order(self) -> list[str]:
        """Get the current agent order.

        Returns:
            List of agent IDs in chain order
        """
        return self.agent_order
