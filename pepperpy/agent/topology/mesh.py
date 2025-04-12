"""
Mesh Topology.

Implements a decentralized agent topology where agents can communicate
directly with each other without a central coordinator.
"""

from typing import Any

from pepperpy.core.logging import get_logger

from .base import AgentTopologyProvider, TopologyError

logger = get_logger(__name__)


class MeshTopology(AgentTopologyProvider):
    """Mesh topology implementation.

    This topology follows a peer-to-peer pattern where agents can communicate
    directly with each other without a central coordinator.

    Mesh topologies are suitable for:
    - Collaborative problem-solving
    - Self-organizing systems
    - Complex multi-agent interactions
    - Redundant/fault-tolerant agent networks

    Configuration:
        routing_policy: How to route messages between agents
        max_iterations: Maximum number of interaction iterations
        agents: Dict of agent configurations by ID
        connections: List of agent connections [from_id, to_id]
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize mesh topology.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.max_iterations = self.config.get("max_iterations", 10)
        self.routing_policy = self.config.get("routing_policy", "all_connected")
        self.connections: list[tuple[str, str]] = self.config.get("connections", [])
        self.routing_table: dict[str, set[str]] = {}
        self.message_buffer: dict[str, list[dict[str, Any]]] = {}

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

                # Initialize message buffer for agent
                self.message_buffer[agent_id] = []

            # Build routing table based on policy
            await self._build_routing_table()

            self.initialized = True
            logger.info(f"Initialized mesh topology with {len(self.agents)} agents")
        except Exception as e:
            logger.error(f"Failed to initialize mesh topology: {e}")
            await self.cleanup()
            raise TopologyError(f"Initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.routing_table = {}
        self.message_buffer = {}
        await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the mesh topology with input data.

        Args:
            input_data: Input containing task details and initial agent

        Returns:
            Execution results
        """
        if not self.initialized:
            await self.initialize()

        # Extract input task and initial agent
        task = input_data.get("task", "")
        if not task:
            raise TopologyError("No task provided in input data")

        initial_agent_id = input_data.get("initial_agent", None)
        if not initial_agent_id and self.agents:
            # If not specified, use first agent
            initial_agent_id = next(iter(self.agents.keys()))

        if not initial_agent_id or initial_agent_id not in self.agents:
            raise TopologyError(f"Invalid initial agent: {initial_agent_id}")

        # Reset message buffers
        for agent_id in self.message_buffer:
            self.message_buffer[agent_id] = []

        # Seed initial message
        self.message_buffer[initial_agent_id].append({
            "from": "user",
            "to": initial_agent_id,
            "content": task,
        })

        # Execute mesh interaction iterations
        iteration = 0
        all_interactions: list[dict[str, Any]] = []
        active = True

        while active and iteration < self.max_iterations:
            iteration += 1
            logger.debug(f"Mesh interaction iteration {iteration}")

            # Process current message buffer
            iteration_interactions = await self._process_message_buffer()
            all_interactions.extend(iteration_interactions)

            # Check if there are any messages to process in next iteration
            active = any(len(messages) > 0 for messages in self.message_buffer.values())

        # Build result
        result = {
            "iterations": iteration,
            "interactions": all_interactions,
            "final_states": {},
        }

        # If reached max iterations but still active
        if active and iteration >= self.max_iterations:
            result["status"] = "timeout"
            result["message"] = f"Reached maximum iterations ({self.max_iterations})"
        else:
            result["status"] = "complete"

        # Collect final state from each agent
        for agent_id, agent in self.agents.items():
            try:
                # Get the most recent response from each agent as final state
                agent_interactions = [
                    i for i in all_interactions if i.get("from") == agent_id
                ]
                if agent_interactions:
                    result["final_states"][agent_id] = agent_interactions[-1].get(
                        "content", ""
                    )
            except Exception as e:
                logger.error(f"Error getting final state from agent {agent_id}: {e}")

        return result

    async def _process_message_buffer(self) -> list[dict[str, Any]]:
        """Process all messages in the buffer.

        Returns:
            List of interactions processed in this iteration
        """
        interactions = []
        new_messages: dict[str, list[dict[str, Any]]] = {
            agent_id: [] for agent_id in self.agents
        }

        # Process messages for each agent
        for agent_id, messages in self.message_buffer.items():
            if not messages or agent_id not in self.agents:
                continue

            agent = self.agents[agent_id]

            # Concatenate all messages for this agent
            combined_message = "\n\n".join([
                f"FROM {msg['from']}: {msg['content']}" for msg in messages
            ])

            try:
                # Process combined message
                response = await agent.process_message(combined_message)

                # Record interaction
                interactions.append({
                    "from": agent_id,
                    "to": "all",  # Default broadcast
                    "content": response,
                    "raw_inputs": messages,
                })

                # Route response to connected agents
                outbound_agents = self.routing_table.get(agent_id, set())
                for target_agent_id in outbound_agents:
                    if target_agent_id in new_messages:
                        new_messages[target_agent_id].append({
                            "from": agent_id,
                            "to": target_agent_id,
                            "content": response,
                        })
            except Exception as e:
                logger.error(f"Error processing messages for agent {agent_id}: {e}")

        # Update message buffer with new messages
        self.message_buffer = new_messages

        return interactions

    async def _build_routing_table(self) -> None:
        """Build the routing table based on policy."""
        self.routing_table = {agent_id: set() for agent_id in self.agents}

        if self.routing_policy == "all_connected":
            # Fully connected mesh - every agent can message every other agent
            for from_id in self.agents:
                for to_id in self.agents:
                    if from_id != to_id:
                        self.routing_table[from_id].add(to_id)

        elif self.routing_policy == "specified":
            # Use explicit connections from configuration
            for from_id, to_id in self.connections:
                if from_id in self.routing_table and to_id in self.agents:
                    self.routing_table[from_id].add(to_id)

        elif self.routing_policy == "one_way_ring":
            # Create a ring where messages flow in one direction
            agent_ids = list(self.agents.keys())
            if len(agent_ids) > 1:
                for i in range(len(agent_ids)):
                    from_id = agent_ids[i]
                    to_id = agent_ids[(i + 1) % len(agent_ids)]
                    self.routing_table[from_id].add(to_id)

        elif self.routing_policy == "two_way_ring":
            # Create a ring where messages flow in both directions
            agent_ids = list(self.agents.keys())
            if len(agent_ids) > 1:
                for i in range(len(agent_ids)):
                    from_id = agent_ids[i]
                    to_id = agent_ids[(i + 1) % len(agent_ids)]
                    self.routing_table[from_id].add(to_id)
                    self.routing_table[to_id].add(from_id)

        logger.debug(f"Built routing table: {self.routing_table}")

    async def add_connection(self, from_agent_id: str, to_agent_id: str) -> None:
        """Add a connection between agents.

        Args:
            from_agent_id: Source agent ID
            to_agent_id: Target agent ID

        Raises:
            TopologyError: If agents don't exist
        """
        if from_agent_id not in self.agents:
            raise TopologyError(f"Source agent {from_agent_id} does not exist")

        if to_agent_id not in self.agents:
            raise TopologyError(f"Target agent {to_agent_id} does not exist")

        if from_agent_id == to_agent_id:
            raise TopologyError("Cannot connect agent to itself")

        if from_agent_id in self.routing_table:
            self.routing_table[from_agent_id].add(to_agent_id)
        else:
            self.routing_table[from_agent_id] = {to_agent_id}

        logger.debug(f"Added connection: {from_agent_id} -> {to_agent_id}")

    async def remove_connection(self, from_agent_id: str, to_agent_id: str) -> None:
        """Remove a connection between agents.

        Args:
            from_agent_id: Source agent ID
            to_agent_id: Target agent ID
        """
        if (
            from_agent_id in self.routing_table
            and to_agent_id in self.routing_table[from_agent_id]
        ):
            self.routing_table[from_agent_id].remove(to_agent_id)
            logger.debug(f"Removed connection: {from_agent_id} -> {to_agent_id}")

    async def get_routing_table(self) -> dict[str, list[str]]:
        """Get the current routing table.

        Returns:
            Dict mapping agent IDs to connected target agent IDs
        """
        return {
            agent_id: list(connections)
            for agent_id, connections in self.routing_table.items()
        }
