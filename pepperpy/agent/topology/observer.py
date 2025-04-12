"""
Observer Topology.

Implements an observer pattern where agents can monitor and react to
the actions of other agents without direct interaction.
"""

from collections.abc import Callable
from typing import Any

from pepperpy.core.logging import get_logger

from .base import AgentTopologyProvider, TopologyError

logger = get_logger(__name__)


class ObserverTopology(AgentTopologyProvider):
    """Observer topology implementation.

    This topology implements the observer pattern where some agents monitor
    the actions of other agents and can react to those actions as needed.

    Useful for:
    - Monitoring and logging agent behavior
    - Audit and compliance scenarios
    - Creating reactive agent systems
    - Building agent oversight mechanisms

    Configuration:
        subscriptions: Dict mapping observer agents to observable agents or events
        broadcast_events: Whether to broadcast all events to all observers
        log_all_events: Whether to log all events for debugging
        allow_interventions: Whether observers can intervene in observable actions
        agents: Dict of agent configurations by ID
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize observer topology.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Observer configuration
        self.subscriptions = self.config.get("subscriptions", {})
        self.broadcast_events = self.config.get("broadcast_events", False)
        self.log_all_events = self.config.get("log_all_events", False)
        self.allow_interventions = self.config.get("allow_interventions", False)

        # Internal state
        self.events: list[dict[str, Any]] = []
        self.observers: dict[str, set[str]] = {}  # observable -> set of observers
        self.event_handlers: dict[
            str, dict[str, list[Callable]]
        ] = {}  # event_type -> (agent_id -> handlers)
        self.interventions: dict[
            str, dict[str, Any]
        ] = {}  # observable -> intervention details

    async def initialize(self) -> None:
        """Initialize observer topology resources."""
        if self.initialized:
            return

        try:
            # Initialize agents from configuration
            for agent_id, agent_config in self.agent_configs.items():
                from pepperpy.agent import create_agent

                agent = create_agent(**agent_config)
                await self.add_agent(agent_id, agent)

            # Build observer relationships from subscriptions
            for observer_id, observables in self.subscriptions.items():
                if observer_id not in self.agents:
                    logger.warning(f"Observer agent {observer_id} not found, skipping")
                    continue

                if isinstance(observables, str):
                    observables = [observables]

                for observable in observables:
                    if observable not in self.agents and observable != "*":
                        logger.warning(
                            f"Observable agent {observable} not found, skipping"
                        )
                        continue

                    if observable not in self.observers:
                        self.observers[observable] = set()

                    self.observers[observable].add(observer_id)
                    logger.debug(f"Agent {observer_id} is now observing {observable}")

            # If broadcast is enabled, add all observers to special "*" category
            if self.broadcast_events:
                self.observers["*"] = set(self.subscriptions.keys())

            self.initialized = True
            logger.info(f"Initialized observer topology with {len(self.agents)} agents")

        except Exception as e:
            logger.error(f"Failed to initialize observer topology: {e}")
            await self.cleanup()
            raise TopologyError(f"Initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up observer topology resources."""
        self.events = []
        self.observers = {}
        self.event_handlers = {}
        self.interventions = {}

        await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the observer topology with input data.

        Args:
            input_data: Input containing task and target agent

        Returns:
            Execution results
        """
        if not self.initialized:
            await self.initialize()

        # Extract task and target agent
        task = input_data.get("task", "")
        if not task:
            raise TopologyError("No task provided in input data")

        target_agent_id = input_data.get("target_agent")
        if not target_agent_id or target_agent_id not in self.agents:
            raise TopologyError(f"Invalid target agent: {target_agent_id}")

        # Check if this agent is being observed
        is_observed = (
            target_agent_id in self.observers
            and len(self.observers[target_agent_id]) > 0
        )

        # Create event for this execution
        event_id = f"event_{len(self.events)}"
        event = {
            "id": event_id,
            "type": "execution",
            "agent_id": target_agent_id,
            "task": task,
            "timestamp": self._get_timestamp(),
            "input_data": input_data,
            "observers": list(self.observers.get(target_agent_id, set())),
            "result": None,
            "interventions": [],
            "status": "pending",
        }

        self.events.append(event)

        if self.log_all_events:
            logger.info(f"Created event {event_id} for agent {target_agent_id}")

        # Check for pre-execution interventions if enabled
        if self.allow_interventions and is_observed:
            await self._check_interventions(event)

        # Execute agent task
        try:
            # Process the task with the target agent
            target_agent = self.agents[target_agent_id]

            # Check if there's a pre-execution intervention
            intervention = self.interventions.get(target_agent_id, {})
            if intervention.get("type") == "prevent_execution":
                # Execution was blocked by an observer
                logger.info(
                    f"Execution prevented for agent {target_agent_id} by observer"
                )
                event["status"] = "blocked"
                event["result"] = {
                    "status": "blocked",
                    "message": intervention.get(
                        "message", "Execution prevented by observer"
                    ),
                    "observer": intervention.get("observer_id"),
                }
            else:
                # Normal execution
                logger.debug(f"Executing task with agent {target_agent_id}")
                result = await target_agent.process_message(task)

                event["result"] = result
                event["status"] = "completed"

                # Notify observers of the execution result
                if is_observed:
                    await self._notify_observers(event)

                # Check if there's a post-execution intervention (result modification)
                if intervention.get("type") == "modify_result":
                    logger.info(
                        f"Result modified for agent {target_agent_id} by observer"
                    )
                    result = intervention.get("modified_result", result)
                    event["interventions"].append({
                        "type": "modify_result",
                        "observer": intervention.get("observer_id"),
                        "timestamp": self._get_timestamp(),
                    })

        except Exception as e:
            logger.error(f"Error executing task with agent {target_agent_id}: {e}")
            event["status"] = "error"
            event["error"] = str(e)

            # Notify observers of the error
            if is_observed:
                await self._notify_observers(event)

            raise TopologyError(f"Failed to execute task: {e}") from e

        # Clear any interventions for this agent
        if target_agent_id in self.interventions:
            del self.interventions[target_agent_id]

        return {
            "status": "success",
            "result": event["result"],
            "agent_id": target_agent_id,
            "event_id": event_id,
            "observers": event["observers"],
            "interventions": event["interventions"],
        }

    def _get_timestamp(self) -> float:
        """Get current timestamp.

        Returns:
            Current timestamp
        """
        import time

        return time.time()

    async def _notify_observers(self, event: dict[str, Any]) -> None:
        """Notify observer agents about an event.

        Args:
            event: Event data to notify about
        """
        # Identify which observers need to be notified
        observers_to_notify = set()

        # Add direct observers of the agent
        if event["agent_id"] in self.observers:
            observers_to_notify.update(self.observers[event["agent_id"]])

        # Add broadcast observers
        if self.broadcast_events and "*" in self.observers:
            observers_to_notify.update(self.observers["*"])

        if not observers_to_notify:
            return

        logger.debug(
            f"Notifying {len(observers_to_notify)} observers about event {event['id']}"
        )

        # Notify each observer
        for observer_id in observers_to_notify:
            if observer_id not in self.agents:
                logger.warning(
                    f"Observer {observer_id} not found, skipping notification"
                )
                continue

            # Create observation message for the observer
            observation = {
                "type": "observation",
                "event_id": event["id"],
                "observed_agent": event["agent_id"],
                "task": event["task"],
                "timestamp": self._get_timestamp(),
                "result": event["result"],
                "status": event["status"],
            }

            # Send observation to observer agent
            observer = self.agents[observer_id]

            observation_message = (
                f"OBSERVATION EVENT:\n"
                f"Agent {event['agent_id']} executed task: {event['task']}\n"
                f"Status: {event['status']}\n"
                f"Result: {str(event['result'])[:500]}...\n"
                f"\nPlease process this observation according to your role."
            )

            try:
                await observer.process_message(observation_message)
                logger.debug(
                    f"Observer {observer_id} notified about event {event['id']}"
                )
            except Exception as e:
                logger.error(f"Failed to notify observer {observer_id}: {e}")

    async def _check_interventions(self, event: dict[str, Any]) -> None:
        """Check if any observers want to intervene before execution.

        Args:
            event: Event data for the planned execution
        """
        if not self.allow_interventions:
            return

        # Identify which observers might intervene
        potential_interveners = set()

        # Add direct observers of the agent
        if event["agent_id"] in self.observers:
            potential_interveners.update(self.observers[event["agent_id"]])

        if not potential_interveners:
            return

        logger.debug(
            f"Checking {len(potential_interveners)} observers for interventions"
        )

        # Check with each observer if they want to intervene
        for observer_id in potential_interveners:
            if observer_id not in self.agents:
                continue

            # Create intervention request message
            intervention_request = (
                f"INTERVENTION REQUEST:\n"
                f"Agent {event['agent_id']} is about to execute task: {event['task']}\n"
                f"\nDo you wish to intervene? Options:\n"
                f"1. ALLOW: Allow execution to proceed normally\n"
                f"2. PREVENT: Block execution of this task\n"
                f"3. MODIFY: Suggest modifications to the task\n"
                f"\nRespond with your choice and reason."
            )

            # Send intervention request to observer
            observer = self.agents[observer_id]

            try:
                response = await observer.process_message(intervention_request)

                # Parse intervention response
                if "PREVENT" in response:
                    # Observer wants to prevent execution
                    self.interventions[event["agent_id"]] = {
                        "type": "prevent_execution",
                        "observer_id": observer_id,
                        "timestamp": self._get_timestamp(),
                        "message": response,
                    }

                    event["interventions"].append({
                        "type": "prevent_execution",
                        "observer": observer_id,
                        "timestamp": self._get_timestamp(),
                    })

                    logger.info(
                        f"Observer {observer_id} prevented execution for agent {event['agent_id']}"
                    )

                    # Once an observer prevents execution, no need to check others
                    break

                elif "MODIFY" in response:
                    # Observer wants to modify the task or result
                    self.interventions[event["agent_id"]] = {
                        "type": "modify_result",
                        "observer_id": observer_id,
                        "timestamp": self._get_timestamp(),
                        "modified_result": response.replace("MODIFY:", "").strip(),
                    }

                    logger.info(
                        f"Observer {observer_id} will modify results for agent {event['agent_id']}"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to check intervention with observer {observer_id}: {e}"
                )

    async def register_event_handler(
        self, agent_id: str, event_type: str, handler: Callable
    ) -> None:
        """Register an event handler for an agent.

        Args:
            agent_id: Agent ID to register handler for
            event_type: Type of event to handle
            handler: Callback function to handle the event

        Raises:
            TopologyError: If agent not found
        """
        if agent_id not in self.agents:
            raise TopologyError(f"Agent {agent_id} not found")

        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = {}

        if agent_id not in self.event_handlers[event_type]:
            self.event_handlers[event_type][agent_id] = []

        self.event_handlers[event_type][agent_id].append(handler)
        logger.debug(
            f"Registered event handler for agent {agent_id}, event type {event_type}"
        )

    async def add_observer(self, observer_id: str, observable_id: str) -> None:
        """Add an observer relationship.

        Args:
            observer_id: ID of the observer agent
            observable_id: ID of the agent to observe

        Raises:
            TopologyError: If agents not found
        """
        if observer_id not in self.agents:
            raise TopologyError(f"Observer agent {observer_id} not found")

        if observable_id != "*" and observable_id not in self.agents:
            raise TopologyError(f"Observable agent {observable_id} not found")

        if observable_id not in self.observers:
            self.observers[observable_id] = set()

        self.observers[observable_id].add(observer_id)
        logger.info(f"Agent {observer_id} is now observing {observable_id}")

    async def remove_observer(self, observer_id: str, observable_id: str) -> None:
        """Remove an observer relationship.

        Args:
            observer_id: ID of the observer agent
            observable_id: ID of the agent being observed

        Raises:
            TopologyError: If relationship not found
        """
        if (
            observable_id not in self.observers
            or observer_id not in self.observers[observable_id]
        ):
            raise TopologyError(
                f"Observer relationship not found: {observer_id} -> {observable_id}"
            )

        self.observers[observable_id].remove(observer_id)
        logger.info(f"Agent {observer_id} is no longer observing {observable_id}")

    async def get_events(
        self, agent_id: str | None = None, event_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Get events filtered by agent and/or type.

        Args:
            agent_id: Filter events by agent ID
            event_type: Filter events by type

        Returns:
            List of matching events
        """
        filtered_events = self.events

        if agent_id:
            filtered_events = [e for e in filtered_events if e["agent_id"] == agent_id]

        if event_type:
            filtered_events = [e for e in filtered_events if e["type"] == event_type]

        return filtered_events

    async def get_observers(self, agent_id: str) -> list[str]:
        """Get all observers for an agent.

        Args:
            agent_id: Agent ID to get observers for

        Returns:
            List of observer agent IDs
        """
        observers = set()

        # Add direct observers
        if agent_id in self.observers:
            observers.update(self.observers[agent_id])

        # Add broadcast observers
        if "*" in self.observers:
            observers.update(self.observers["*"])

        return list(observers)

    async def get_observables(self, observer_id: str) -> list[str]:
        """Get all agents observed by an observer.

        Args:
            observer_id: Observer agent ID

        Returns:
            List of observable agent IDs
        """
        observables = []

        for observable, observers in self.observers.items():
            if observer_id in observers:
                observables.append(observable)

        return observables
