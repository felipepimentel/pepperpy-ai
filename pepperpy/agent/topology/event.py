"""
Event Topology.

Implements an event-based agent topology where agents communicate through
a publish-subscribe pattern using events and topics.
"""

from collections import defaultdict
from typing import Any

from pepperpy.core.logging import get_logger

from .base import AgentTopologyProvider, TopologyError

logger = get_logger(__name__)


class EventTopology(AgentTopologyProvider):
    """Event-based topology implementation.

    This topology follows a publish-subscribe pattern where agents communicate
    by publishing events to topics and subscribing to topics of interest.

    Event topologies are suitable for:
    - Loosely coupled agent systems
    - Event-driven workflows
    - Systems with dynamic agent participation
    - High scalability requirements

    Configuration:
        max_iterations: Maximum number of event processing iterations
        agents: Dict of agent configurations by ID
        topic_subscriptions: Initial topic subscriptions {topic: [agent_ids]}
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize event topology.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.max_iterations = self.config.get("max_iterations", 10)
        self.topic_subscriptions: dict[str, set[str]] = defaultdict(set)

        # Initialize from config
        topic_subs = self.config.get("topic_subscriptions", {})
        for topic, agent_ids in topic_subs.items():
            for agent_id in agent_ids:
                self.topic_subscriptions[topic].add(agent_id)

        self.event_queue: list[dict[str, Any]] = []

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

            self.initialized = True
            logger.info(f"Initialized event topology with {len(self.agents)} agents")
        except Exception as e:
            logger.error(f"Failed to initialize event topology: {e}")
            await self.cleanup()
            raise TopologyError(f"Initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.topic_subscriptions = defaultdict(set)
        self.event_queue = []
        await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the event topology with input data.

        Args:
            input_data: Input containing task and topic

        Returns:
            Execution results
        """
        if not self.initialized:
            await self.initialize()

        # Extract input task and topic
        task = input_data.get("task", "")
        if not task:
            raise TopologyError("No task provided in input data")

        topic = input_data.get("topic", "input")

        # Reset event queue
        self.event_queue = []

        # Publish initial event
        await self.publish_event(
            topic,
            {
                "from": "user",
                "content": task,
                "metadata": input_data.get("metadata", {}),
            },
        )

        # Execute event processing iterations
        iteration = 0
        all_events: list[dict[str, Any]] = []

        while self.event_queue and iteration < self.max_iterations:
            iteration += 1
            logger.debug(
                f"Event processing iteration {iteration} with {len(self.event_queue)} events"
            )

            # Process current event queue
            current_queue = self.event_queue.copy()
            self.event_queue = []  # Clear for new events

            for event in current_queue:
                await self._process_event(event)
                all_events.append(event)

        # Build result
        result = {"iterations": iteration, "events": all_events, "final_states": {}}

        # If reached max iterations but still have events
        if self.event_queue and iteration >= self.max_iterations:
            result["status"] = "timeout"
            result["message"] = f"Reached maximum iterations ({self.max_iterations})"
            result["pending_events"] = len(self.event_queue)
        else:
            result["status"] = "complete"

        # Collect final state from relevant events
        for agent_id in self.agents:
            # Find the most recent event published by this agent
            agent_events = [e for e in all_events if e.get("publisher") == agent_id]
            if agent_events:
                result["final_states"][agent_id] = (
                    agent_events[-1].get("data", {}).get("content", "")
                )

        return result

    async def _process_event(self, event: dict[str, Any]) -> None:
        """Process a single event by routing to subscribed agents.

        Args:
            event: Event data
        """
        topic = event.get("topic", "")
        subscriber_ids = self.topic_subscriptions.get(topic, set())

        if not subscriber_ids:
            logger.debug(f"No subscribers for topic {topic}")
            return

        for agent_id in subscriber_ids:
            if agent_id not in self.agents:
                continue

            agent = self.agents[agent_id]
            event_data = event.get("data", {})

            # Format event data for agent consumption
            message = (
                f"EVENT ({topic})\n"
                f"FROM: {event_data.get('from', 'system')}\n"
                f"CONTENT: {event_data.get('content', '')}"
            )

            try:
                # Process event message
                response = await agent.process_message(message)

                # Determine if agent wants to publish a response
                # This is a simple heuristic - in a real system, we might
                # use a more structured protocol for agent responses
                topic_marker = "PUBLISH TO:"
                if topic_marker in response:
                    # Extract publish topic
                    lines = response.split("\n")
                    for i, line in enumerate(lines):
                        if topic_marker in line:
                            pub_topic = line.split(topic_marker, 1)[1].strip()
                            content = "\n".join(lines[i + 1 :]).strip()

                            # Publish to extracted topic
                            await self.publish_event(
                                pub_topic,
                                {
                                    "from": agent_id,
                                    "content": content,
                                    "in_response_to": topic,
                                },
                            )
                            break
                else:
                    # Default publish to agent's output topic
                    await self.publish_event(
                        f"{agent_id}_output",
                        {
                            "from": agent_id,
                            "content": response,
                            "in_response_to": topic,
                        },
                    )

            except Exception as e:
                logger.error(f"Error processing event for agent {agent_id}: {e}")

    async def publish_event(
        self, topic: str, data: dict[str, Any], publisher: str = "system"
    ) -> None:
        """Publish an event to a topic.

        Args:
            topic: Topic to publish to
            data: Event data
            publisher: ID of the publishing entity
        """
        event = {
            "topic": topic,
            "publisher": publisher,
            "data": data,
            "timestamp": self._get_timestamp(),
        }

        self.event_queue.append(event)
        logger.debug(
            f"Published event to topic '{topic}' (queue size: {len(self.event_queue)})"
        )

    async def subscribe(self, agent_id: str, topic: str) -> None:
        """Subscribe an agent to a topic.

        Args:
            agent_id: Agent ID
            topic: Topic to subscribe to

        Raises:
            TopologyError: If agent doesn't exist
        """
        if agent_id not in self.agents:
            raise TopologyError(f"Agent {agent_id} does not exist")

        self.topic_subscriptions[topic].add(agent_id)
        logger.debug(f"Agent {agent_id} subscribed to topic '{topic}'")

    async def unsubscribe(self, agent_id: str, topic: str) -> None:
        """Unsubscribe an agent from a topic.

        Args:
            agent_id: Agent ID
            topic: Topic to unsubscribe from
        """
        if (
            topic in self.topic_subscriptions
            and agent_id in self.topic_subscriptions[topic]
        ):
            self.topic_subscriptions[topic].remove(agent_id)
            logger.debug(f"Agent {agent_id} unsubscribed from topic '{topic}'")

            # Remove empty topics
            if not self.topic_subscriptions[topic]:
                del self.topic_subscriptions[topic]

    async def get_subscriptions(self) -> dict[str, list[str]]:
        """Get all topic subscriptions.

        Returns:
            Dict mapping topics to lists of subscribed agent IDs
        """
        return {
            topic: list(agent_ids)
            for topic, agent_ids in self.topic_subscriptions.items()
        }

    async def get_agent_subscriptions(self, agent_id: str) -> list[str]:
        """Get all topics an agent is subscribed to.

        Args:
            agent_id: Agent ID

        Returns:
            List of subscribed topics

        Raises:
            TopologyError: If agent doesn't exist
        """
        if agent_id not in self.agents:
            raise TopologyError(f"Agent {agent_id} does not exist")

        return [
            topic
            for topic, agent_ids in self.topic_subscriptions.items()
            if agent_id in agent_ids
        ]

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().isoformat()
