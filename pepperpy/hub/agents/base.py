"""Base classes for AI agents.

This module provides the base classes and utilities for creating AI agents.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from uuid import uuid4

from pepperpy.monitoring import logger
from pepperpy.providers.base import Provider

T = TypeVar("T")


class ThoughtType(Enum):
    """Types of agent thoughts."""

    REASONING = auto()  # General reasoning
    PLANNING = auto()  # Planning next steps
    OBSERVATION = auto()  # Observing state/environment
    EXECUTION = auto()  # Executing actions
    REFLECTION = auto()  # Reflecting on results
    ERROR = auto()  # Error handling
    INTERVENTION = auto()  # User intervention needed


class AgentStatus(Enum):
    """Agent execution status."""

    INITIALIZING = auto()  # Starting up
    RUNNING = auto()  # Normal execution
    PAUSED = auto()  # Temporarily paused
    WAITING = auto()  # Waiting for input/resources
    COMPLETED = auto()  # Successfully completed
    FAILED = auto()  # Failed execution
    CANCELLED = auto()  # Cancelled by user


@dataclass
class AgentThought:
    """Represents an agent's thought process.

    Attributes:
        id: Unique thought identifier
        type: Type of thought (reasoning, planning, etc.)
        content: The actual thought content
        timestamp: When the thought occurred
        metadata: Additional context about the thought
        parent_id: Optional ID of parent thought
        children: List of child thought IDs

    """

    id: str = field(default_factory=lambda: str(uuid4()))
    type: ThoughtType = ThoughtType.REASONING
    content: str = ""
    timestamp: float = field(default_factory=lambda: time.time())
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)


@dataclass
class AgentProgress:
    """Tracks agent progress during execution.

    Attributes:
        step: Current execution step
        progress: Progress from 0.0 to 1.0
        status: Current execution status
        message: Status message
        timestamp: Last update time
        steps_completed: List of completed steps
        steps_remaining: List of remaining steps
        estimated_completion: Estimated completion timestamp

    """

    step: str = ""
    progress: float = 0.0  # 0.0 to 1.0
    status: AgentStatus = AgentStatus.INITIALIZING
    message: str = ""
    timestamp: float = field(default_factory=lambda: time.time())
    steps_completed: List[str] = field(default_factory=list)
    steps_remaining: List[str] = field(default_factory=list)
    estimated_completion: Optional[float] = None


@dataclass
class AgentSession:
    """Manages agent execution session.

    Attributes:
        id: Unique session identifier
        agent_id: ID of the executing agent
        task: Task being executed
        thoughts: List of agent thoughts
        progress: Current progress state
        metadata: Session metadata
        needs_intervention: Whether user intervention is needed
        intervention_prompt: Optional prompt for user intervention
        start_time: Session start timestamp
        end_time: Optional session end timestamp

    """

    id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    task: str = ""
    thoughts: List[AgentThought] = field(default_factory=list)
    progress: AgentProgress = field(default_factory=AgentProgress)
    metadata: Dict[str, Any] = field(default_factory=dict)
    needs_intervention: bool = False
    intervention_prompt: Optional[str] = None
    start_time: float = field(default_factory=lambda: time.time())
    end_time: Optional[float] = None

    def add_thought(
        self,
        content: str,
        type: Union[ThoughtType, str] = ThoughtType.REASONING,
        parent_id: Optional[str] = None,
        **metadata: Any,
    ) -> str:
        """Add a thought to the session.

        Args:
            content: The thought content
            type: Type of thought
            parent_id: Optional parent thought ID
            **metadata: Additional thought metadata

        Returns:
            ID of the created thought

        """
        # Convert string type to enum if needed
        if isinstance(type, str):
            type = ThoughtType[type.upper()]

        thought = AgentThought(
            content=content, type=type, parent_id=parent_id, metadata=metadata
        )

        # Update parent's children if exists
        if parent_id:
            for parent in self.thoughts:
                if parent.id == parent_id:
                    parent.children.append(thought.id)
                    break

        self.thoughts.append(thought)
        return thought.id

    def update_progress(
        self,
        step: str,
        progress: float,
        status: Union[AgentStatus, str] = AgentStatus.RUNNING,
        message: str = "",
        completed_step: Optional[str] = None,
        remaining_steps: Optional[List[str]] = None,
        estimated_completion: Optional[float] = None,
    ) -> None:
        """Update session progress.

        Args:
            step: Current execution step
            progress: Progress value (0.0-1.0)
            status: Execution status
            message: Status message
            completed_step: Optional step that was just completed
            remaining_steps: Optional list of remaining steps
            estimated_completion: Optional estimated completion time

        """
        # Convert string status to enum if needed
        if isinstance(status, str):
            status = AgentStatus[status.upper()]

        # Update completed steps
        if completed_step:
            if completed_step not in self.progress.steps_completed:
                self.progress.steps_completed.append(completed_step)
            if completed_step in self.progress.steps_remaining:
                self.progress.steps_remaining.remove(completed_step)

        # Update remaining steps
        if remaining_steps is not None:
            self.progress.steps_remaining = remaining_steps

        self.progress = AgentProgress(
            step=step,
            progress=progress,
            status=status,
            message=message,
            steps_completed=self.progress.steps_completed,
            steps_remaining=self.progress.steps_remaining,
            estimated_completion=estimated_completion,
        )

        # Update session end time if completed or failed
        if status in (AgentStatus.COMPLETED, AgentStatus.FAILED):
            self.end_time = time.time()

    def request_intervention(self, prompt: str) -> None:
        """Request user intervention.

        Args:
            prompt: Message explaining what input is needed

        """
        self.needs_intervention = True
        self.intervention_prompt = prompt
        self.progress.status = AgentStatus.WAITING

    def provide_intervention(self, response: str) -> None:
        """Handle user intervention response.

        Args:
            response: User's response to intervention request

        """
        self.needs_intervention = False
        self.intervention_prompt = None
        self.progress.status = AgentStatus.RUNNING
        self.add_thought(
            f"Received user intervention: {response}",
            type=ThoughtType.INTERVENTION,
            response=response,
        )


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""

    provider: Optional[Provider] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    name: str = "Unnamed Agent"
    description: str = "No description provided"
    version: str = "0.1.0"
    capabilities: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default values for parameters."""
        if not isinstance(self.parameters, dict):
            self.parameters = {}
        if not isinstance(self.capabilities, list):
            self.capabilities = []

    def update(self, config: Dict[str, Any]) -> "AgentConfig":
        """Create a new config with updated values.

        Args:
            config: New configuration values to apply

        Returns:
            A new AgentConfig instance with updated values

        """
        # Create new config with current values
        new_config = AgentConfig(
            provider=self.provider,
            parameters=dict(self.parameters),
            name=self.name,
            description=self.description,
            version=self.version,
            capabilities=list(self.capabilities),
        )

        # Update with new values
        if "provider" in config:
            new_config.provider = config["provider"]
        if "parameters" in config:
            new_config.parameters.update(config["parameters"])
        if "name" in config:
            new_config.name = config["name"]
        if "description" in config:
            new_config.description = config["description"]
        if "version" in config:
            new_config.version = config["version"]
        if "capabilities" in config:
            new_config.capabilities.extend(config["capabilities"])

        return new_config


def require_provider(f):
    """Decorator to ensure provider is configured before executing method."""

    @wraps(f)
    async def wrapper(self, *args, **kwargs):
        if not self.config.provider:
            raise ValueError(f"No provider configured for agent {self.config.name}")
        return await f(self, *args, **kwargs)

    return wrapper


class Agent(ABC, Generic[T]):
    """Base class for AI agents with enhanced functionality.

    This class provides:
    - Thought process tracking
    - Progress monitoring
    - Session management
    - User intervention handling
    - Resource cleanup
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize the agent.

        Args:
            config: Configuration for the agent.

        """
        self.config = config
        self.log = logger.bind(agent=config.name)
        self._session: Optional[AgentSession] = None
        self._execution_steps: List[str] = []

    @property
    def name(self) -> str:
        """Get agent name."""
        return self.config.name

    @property
    def description(self) -> str:
        """Get agent description."""
        return self.config.description

    @property
    def version(self) -> str:
        """Get agent version."""
        return self.config.version

    @property
    def capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.config.capabilities

    @property
    def session(self) -> Optional[AgentSession]:
        """Get current session if active."""
        return self._session

    async def start_session(self, task: str) -> AgentSession:
        """Start a new execution session.

        Args:
            task: The task to execute

        Returns:
            The created session

        Example:
            >>> async with agent.run("Research AI") as session:
            ...     print(session.current_step)
            ...     print(session.thoughts)
            ...     if session.needs_intervention:
            ...         session.provide_intervention("More details")

        """
        if self._session:
            await self.end_session()

        # Create new session
        self._session = AgentSession(agent_id=self.name, task=task)

        # Add initial thought
        self._session.add_thought(
            f"Starting task: {task}",
            type=ThoughtType.PLANNING,
            task=task,
            capabilities=self.capabilities,
        )

        # Initialize progress
        if self._execution_steps:
            self._session.update_progress(
                step="initialize",
                progress=0.0,
                status=AgentStatus.INITIALIZING,
                message="Starting task execution",
                remaining_steps=self._execution_steps.copy(),
            )

        return self._session

    async def end_session(self) -> None:
        """End the current session."""
        if self._session:
            # Add final thought
            if self._session.progress.status not in (
                AgentStatus.COMPLETED,
                AgentStatus.FAILED,
                AgentStatus.CANCELLED,
            ):
                self._session.add_thought(
                    "Session ended without completion", type=ThoughtType.REFLECTION
                )
                self._session.update_progress(
                    step="end",
                    progress=1.0,
                    status=AgentStatus.CANCELLED,
                    message="Session ended",
                )
            self._session = None

    @require_provider
    async def execute(self, prompt: str, **kwargs) -> str:
        """Execute the agent with a given prompt.

        This method supports:
        - Thought process tracking
        - Progress monitoring
        - Error handling
        - User intervention
        """
        self.log.debug("Executing prompt", prompt=prompt[:100] + "...")

        if self._session:
            # Record execution thought
            thought_id = self._session.add_thought(
                f"Executing prompt: {prompt[:100]}...",
                type=ThoughtType.EXECUTION,
                **kwargs,
            )

            # Update progress
            self._session.update_progress(
                step="execute",
                progress=0.5,
                status=AgentStatus.RUNNING,
                message="Processing prompt",
            )

            try:
                # Execute with provider
                params = {**self.config.parameters, **kwargs}
                assert self.config.provider is not None  # for type checker
                result = await self.config.provider.generate(prompt, params)

                # Record success thought
                self._session.add_thought(
                    "Execution completed successfully",
                    type=ThoughtType.REFLECTION,
                    parent_id=thought_id,
                    result_length=len(result),
                )

                # Update progress
                self._session.update_progress(
                    step="execute",
                    progress=1.0,
                    status=AgentStatus.COMPLETED,
                    message="Prompt execution completed",
                    completed_step="execute",
                )

                return result

            except Exception as e:
                # Record error thought
                self._session.add_thought(
                    f"Execution failed: {str(e)}",
                    type=ThoughtType.ERROR,
                    parent_id=thought_id,
                    error=str(e),
                )

                # Update progress
                self._session.update_progress(
                    step="execute",
                    progress=1.0,
                    status=AgentStatus.FAILED,
                    message=f"Execution failed: {str(e)}",
                )

                raise

        else:
            # Execute without session tracking
            params = {**self.config.parameters, **kwargs}
            assert self.config.provider is not None  # for type checker
            return await self.config.provider.generate(prompt, params)

    def set_execution_steps(self, steps: List[str]) -> None:
        """Set the execution steps for progress tracking.

        Args:
            steps: List of execution step names

        """
        self._execution_steps = steps

    async def request_user_input(self, prompt: str) -> str:
        """Request input from the user.

        Args:
            prompt: Message explaining what input is needed

        Returns:
            User's response

        Raises:
            RuntimeError: If no active session

        """
        if not self._session:
            raise RuntimeError("No active session")

        # Request intervention
        self._session.request_intervention(prompt)

        # Wait for response (in real implementation, this would be async)
        # For now, we'll use a simple input
        response = input(f"\n[{self.name}] {prompt}: ")

        # Handle response
        self._session.provide_intervention(response)
        return response

    @abstractmethod
    async def run(self, input_data: T) -> Any:
        """Run the agent's main functionality.

        This method should be implemented by each agent to provide
        a high-level interface to its capabilities.

        Args:
        ----
            input_data: Input data for the agent.

        Returns:
        -------
            The agent's output.

        """
        raise NotImplementedError

    async def run_sync(self, input_data: T) -> Any:
        """Synchronous version of run method.

        This is a convenience method for users who don't want to deal
        with async/await syntax.

        Args:
        ----
            input_data: Input data for the agent.

        Returns:
        -------
            The agent's output.

        """
        import asyncio

        return asyncio.run(self.run(input_data))

    def validate_capabilities(self, required: List[str]) -> None:
        """Validate that the agent has the required capabilities.

        Args:
        ----
            required: List of required capability names.

        Raises:
        ------
            ValueError: If any required capability is missing.

        """
        missing = [cap for cap in required if cap not in self.capabilities]
        if missing:
            raise ValueError(
                f"Agent {self.name} missing required capabilities: {missing}"
            )

    async def __aenter__(self) -> "Agent":
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self.end_session()

    def __str__(self) -> str:
        """Get string representation of the agent."""
        return f"{self.name} (v{self.version})"

    def __repr__(self) -> str:
        """Get detailed string representation of the agent."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"version='{self.version}', "
            f"capabilities={self.capabilities}"
            f")"
        )

    async def extend(self, config: Dict[str, Any]) -> "Agent":
        """Extend the agent with additional configuration.

        This method creates a new agent instance with the combined
        configuration of this agent and the provided config.

        Args:
            config: Additional configuration to apply

        Returns:
            A new agent instance with the combined configuration

        Example:
            >>> base_agent = await hub.agent("researcher")
            >>> custom_agent = await base_agent.extend({
            ...     "style": "technical",
            ...     "depth": "deep"
            ... })

        """
        # Create new config with updated values
        new_config = self.config.update(config)

        # Create new instance with combined config
        return self.__class__(new_config)


class AgentRegistry:
    """Registry for managing and loading agents."""

    _agents: Dict[str, Dict[str, Agent]] = {}

    @classmethod
    def register(cls, name: str, agent: Agent, version: Optional[str] = None) -> None:
        """Register an agent.

        Args:
        ----
            name: Name to register the agent under.
            agent: The agent instance to register.
            version: Optional version string.

        """
        if name not in cls._agents:
            cls._agents[name] = {}

        version = version or agent.version
        cls._agents[name][version] = agent

    @classmethod
    def get(cls, name: str, version: Optional[str] = None) -> Agent:
        """Get a registered agent by name and version.

        Args:
        ----
            name: Name of the agent to get.
            version: Optional version string.

        Returns:
        -------
            The registered agent.

        Raises:
        ------
            KeyError: If no agent is registered with the given name/version.

        """
        if name not in cls._agents:
            raise KeyError(f"No agent registered with name: {name}")

        agents = cls._agents[name]
        if not version:
            # Get latest version
            version = max(agents.keys())

        if version not in agents:
            raise KeyError(
                f"No agent version {version} found for {name}. "
                f"Available versions: {list(agents.keys())}"
            )

        return agents[version]

    @classmethod
    def list(cls) -> Dict[str, Dict[str, Agent]]:
        """List all registered agents.

        Returns
        -------
            Dictionary of registered agents by name and version.

        """
        return cls._agents.copy()
