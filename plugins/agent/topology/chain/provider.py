"""
Chain Topology Provider.

Implements a sequential agent topology where tasks flow through agents
in a predefined order, like a processing pipeline.
"""

from typing import Any

from pepperpy.agent.topology.base import AgentTopologyProvider, TopologyError
from pepperpy.plugin.provider import BasePluginProvider


class ChainTopologyProvider(AgentTopologyProvider, BasePluginProvider):
    """Chain topology provider.

    Implements a sequential approach to agent coordination where agents process
    tasks in a predefined order, much like a processing pipeline or assembly line.

    This topology is suitable for:
    - Sequential processing tasks
    - Gradual refinement of outputs
    - Multi-step transformation workflows
    - Step-by-step reasoning processes
    """

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        """
        # Use base class initialization first
        await super().initialize()

        if self.initialized:
            return

        # Get configuration
        self.chain_direction = self.config.get("chain_direction", "linear")
        self.max_iterations = self.config.get("max_iterations", 3)
        self.agent_order = self.config.get("agent_order", [])
        self.agent_configs = self.config.get("agents", {})

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

            self.logger.info(
                f"Initialized chain topology with {len(self.agents)} agents"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize chain topology: {e}")
            await self.cleanup()
            raise TopologyError(f"Initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources used by the provider."""
        # Cleanup specific resources
        try:
            # Clean up any agents that were created
            if hasattr(self, "agents") and self.agents:
                for agent_id, agent in list(self.agents.items()):
                    try:
                        if hasattr(agent, "cleanup"):
                            await agent.cleanup()
                    except Exception as e:
                        self.logger.warning(f"Error cleaning up agent {agent_id}: {e}")
        except Exception as e:
            self.logger.error(f"Error during chain topology cleanup: {e}")

        # Always call the base class cleanup last
        await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task based on input data.

        Args:
            input_data: Task data containing:
                - task: The task to execute (run_chain, set_agent_order, get_agent_order)
                - content: Task content (for run_chain)
                - agent_order: New agent order (for set_agent_order)

        Returns:
            Task execution result
        """
        if not self.initialized:
            await self.initialize()

        # Get task type from input
        task_type = input_data.get("task")

        if not task_type:
            return {"status": "error", "message": "No task specified"}

        try:
            if task_type == "run_chain":
                content = input_data.get("content")
                if not content:
                    return {
                        "status": "error",
                        "message": "No content provided for chain execution",
                    }

                # Execute chain process
                if self.chain_direction == "bidirectional":
                    result = await self._execute_bidirectional_chain(
                        content, input_data
                    )
                else:
                    result = await self._execute_linear_chain(content, input_data)

                return result

            elif task_type == "set_agent_order":
                agent_order = input_data.get("agent_order", [])
                if not agent_order:
                    return {"status": "error", "message": "No agent_order provided"}

                try:
                    await self.set_agent_order(agent_order)
                    return {
                        "status": "success",
                        "message": f"Agent order updated: {' -> '.join(agent_order)}",
                    }
                except Exception as e:
                    return {"status": "error", "message": str(e)}

            elif task_type == "get_agent_order":
                agent_order = await self.get_agent_order()
                return {"status": "success", "agent_order": agent_order}

            else:
                return {"status": "error", "message": f"Unknown task: {task_type}"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "message": str(e)}

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
        # Validate chain
        if not self.agent_order:
            raise TopologyError("No agents in chain order")

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
                    chain_steps.append(
                        {
                            "iteration": iteration,
                            "agent_id": agent_id,
                            "input": current_input,
                            "output": result,
                        }
                    )

                    # Update for next step
                    current_input = result
                    final_output = result
                except Exception as e:
                    self.logger.error(f"Error in agent {agent_id}: {e}")
                    chain_steps.append(
                        {
                            "iteration": iteration,
                            "agent_id": agent_id,
                            "input": current_input,
                            "error": str(e),
                        }
                    )

                    # Skip to completion with error if chain breaks
                    return {
                        "status": "error",
                        "steps": chain_steps,
                        "result": f"Chain broken at agent {agent_id}: {e}",
                        "iterations_completed": iteration,
                    }

        # Return successful completion
        return {
            "status": "success",
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
        # Validate chain
        if not self.agent_order:
            raise TopologyError("No agents in chain order")

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
                    chain_steps.append(
                        {
                            "iteration": iteration,
                            "direction": "forward",
                            "agent_id": agent_id,
                            "input": current_input,
                            "output": result,
                        }
                    )

                    # Update for next step
                    current_input = result
                    final_output = result
                except Exception as e:
                    self.logger.error(f"Error in forward pass, agent {agent_id}: {e}")
                    chain_steps.append(
                        {
                            "iteration": iteration,
                            "direction": "forward",
                            "agent_id": agent_id,
                            "input": current_input,
                            "error": str(e),
                        }
                    )

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
                    chain_steps.append(
                        {
                            "iteration": iteration,
                            "direction": "backward",
                            "agent_id": agent_id,
                            "input": current_input,
                            "output": result,
                        }
                    )

                    # Update for next step
                    current_input = result
                    final_output = result
                except Exception as e:
                    self.logger.error(f"Error in backward pass, agent {agent_id}: {e}")
                    chain_steps.append(
                        {
                            "iteration": iteration,
                            "direction": "backward",
                            "agent_id": agent_id,
                            "input": current_input,
                            "error": str(e),
                        }
                    )

                    # Skip to completion with error if chain breaks
                    return {
                        "status": "error",
                        "steps": chain_steps,
                        "result": f"Chain broken at backward pass, agent {agent_id}: {e}",
                        "iterations_completed": iteration,
                    }

        # Return successful completion
        return {
            "status": "success",
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
        self.logger.info(f"Updated chain order: {' -> '.join(self.agent_order)}")

    async def get_agent_order(self) -> list[str]:
        """Get the current agent order.

        Returns:
            List of agent IDs in chain order
        """
        return self.agent_order
