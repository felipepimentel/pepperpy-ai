"""Workflow management for Pepperpy agents."""

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Optional,
    Protocol,
    TypeVar,
    cast,
    runtime_checkable,
)

from pydantic import BaseModel, Field

from pepperpy.core.client import PepperpyClient
from pepperpy.hub.protocols import WorkflowProtocol

if TYPE_CHECKING:
    from pepperpy.hub.sessions import WorkflowSession

T = TypeVar("T", bound="Workflow")


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol defining required agent methods."""

    async def run(self, action: str, **kwargs: Any) -> Any:
        """Run an action on the agent."""
        ...

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        ...


class WorkflowStep(BaseModel):
    """A single step in a workflow.

    Attributes:
        use: Agent to use for this step
        action: Action to perform
        if_: Condition for running this step
        inputs: Input mappings
        outputs: Output mappings

    """

    use: str
    action: str
    if_: Optional[str] = Field(None, alias="if")
    inputs: Dict[str, str] = Field(default_factory=dict)
    outputs: Dict[str, str] = Field(default_factory=dict)


class WorkflowConfig(BaseModel):
    """Configuration for a workflow.

    Attributes:
        name: Workflow name
        steps: List of workflow steps
        inputs: Input mappings
        outputs: Output mappings

    """

    name: str
    steps: list[Dict[str, Any]]
    inputs: Dict[str, str] = Field(default_factory=dict)
    outputs: Dict[str, str] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Dictionary representation of the config

        """
        return self.model_dump()


class Workflow(WorkflowProtocol):
    """A workflow that coordinates multiple agents.

    Workflows define a sequence of steps to be executed by different
    agents, with optional conditions and data passing between steps.
    """

    def __init__(
        self,
        client: PepperpyClient,
        config: WorkflowConfig,
        agents: Dict[str, AgentProtocol],
    ):
        """Initialize a workflow.

        Args:
            client: The Pepperpy client
            config: Workflow configuration
            agents: Map of agent names to instances

        """
        self._client = client
        self._config = config
        self._agents = agents
        self._context: Dict[str, Any] = {}
        self._session: Optional["WorkflowSession"] = None

    @classmethod
    async def from_config(
        cls, client: PepperpyClient, config_path: Path
    ) -> "WorkflowProtocol":
        """Create a workflow from a configuration file.

        Args:
            client: The Pepperpy client
            config_path: Path to workflow configuration file

        Returns:
            The configured workflow instance

        Example:
            >>> flow = await Workflow.from_config(client, "path/to/workflow.yaml")
            >>> async with flow.run("Research AI") as session:
            ...     print(session.current_step)

        """
        import yaml

        with open(config_path) as f:
            raw_config = yaml.safe_load(f)

        config = WorkflowConfig(**raw_config)

        # Load agents
        agents = {}
        for step in config.steps:
            agent_name = step.get("use")
            if agent_name and agent_name not in agents:
                agent = await client.create_agent(agent_name)
                agents[agent_name] = cast(AgentProtocol, agent)

        return cls(client, config, agents)

    async def run(self, task: str, **kwargs: Any) -> Any:
        """Run the workflow.

        Args:
            task: The task to perform
            **kwargs: Additional task parameters

        Returns:
            The final workflow result

        Example:
            >>> flow = await hub.workflow("research-flow")
            >>> async with flow.run("Research AI") as session:
            ...     print(session.current_step)

        """
        # Initialize context
        self._context = {
            "task": task,
            "input": kwargs,
            "steps": {},
        }

        # Create session for tracking progress
        from pepperpy.hub.sessions import WorkflowSession

        session = WorkflowSession(cast(WorkflowProtocol, self))

        # Run each step
        result = None
        for i, step in enumerate(self._config.steps):
            # Check condition
            condition = step.get("if")
            if not self._evaluate_condition(condition):
                continue

            # Get agent
            agent = self._agents[step["use"]]

            # Prepare inputs
            inputs = self._prepare_inputs(step, kwargs)

            # Run step
            result = await agent.run(step["action"], **inputs)

            # Store outputs
            self._store_outputs(step, result, i)

            # Update session
            session.record_step_result(result)

        return result

    def _evaluate_condition(self, condition: Optional[str]) -> bool:
        """Evaluate a step condition.

        Args:
            condition: The condition to evaluate, or None

        Returns:
            True if the condition is met or None, False otherwise

        """
        if not condition:
            return True

        # Basic condition evaluation
        try:
            # Replace variables with values from context
            expr = condition
            for key, value in self._context.items():
                expr = expr.replace(f"{key}.", f"self._context['{key}'].")
            return bool(eval(expr))  # nosec
        except Exception:
            return False

    def _prepare_inputs(
        self, step: Dict[str, Any], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare inputs for a step."""
        inputs = kwargs.copy()

        # Apply input mappings
        for target, source in step["inputs"].items():
            try:
                # Get value from context
                parts = source.split(".")
                value = self._context
                for part in parts:
                    value = value[part]
                inputs[target] = value
            except (KeyError, TypeError):
                continue

        return inputs

    def _store_outputs(
        self, step: Dict[str, Any], result: Any, step_index: int
    ) -> None:
        """Store step outputs in context."""
        # Store full result
        self._context["steps"][f"step_{step_index}"] = result

        # Apply output mappings
        for target, source in step["outputs"].items():
            try:
                # Get value from result
                parts = source.split(".")
                value = result
                for part in parts:
                    value = value[part]
                self._context[target] = value
            except (KeyError, TypeError):
                continue

    async def __aenter__(self) -> "WorkflowSession":
        """Start a workflow session.

        Returns:
            A session for monitoring workflow progress

        """
        if not self._session:
            from pepperpy.hub.sessions import WorkflowSession

            self._session = WorkflowSession(cast(WorkflowProtocol, self))
        return self._session

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up workflow resources."""
        # Clean up agents
        for agent in self._agents.values():
            await agent.cleanup()

        # Clear session
        self._session = None


__all__ = ["Workflow", "WorkflowConfig", "WorkflowStep", "AgentProtocol"]
