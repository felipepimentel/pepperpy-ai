"""Agent interfaces and data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypedDict


class AgentConfig(TypedDict, total=False):
    """Agent configuration type.

    Required fields:
    - agent_id: Unique identifier for the agent
    - model_name: Name of the model to use

    Optional fields:
    - temperature: Sampling temperature (default: 0.7)
    - max_tokens: Maximum tokens to generate (default: 1000)
    - stop_sequences: List of sequences to stop generation (default: [])
    - model_kwargs: Additional model-specific parameters
    """

    agent_id: str
    model_name: str
    temperature: float
    max_tokens: int
    stop_sequences: list[str]
    model_kwargs: dict[str, Any]


@dataclass
class AgentAction:
    """Action taken by an agent.

    Attributes:
        name: Name of the action
        args: Arguments for the action
        confidence: Confidence score (0-1)
        timestamp: When the action was created
        metadata: Additional action metadata
    """

    name: str
    args: dict[str, Any]
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Response from an agent.

    Attributes:
        response: Main response text
        thought_process: List of thoughts leading to response
        actions: List of actions taken
        error: Error message if processing failed
        metadata: Additional response metadata
    """

    response: str
    thought_process: list[str]
    actions: list[AgentAction]
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMemory:
    """Memory entry for an agent.

    Attributes:
        content: Memory content
        source: Source of the memory
        timestamp: When the memory was created
        relevance: Relevance score (0-1)
        metadata: Additional memory metadata
    """

    content: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    relevance: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    """Context for agent processing.

    Attributes:
        conversation_id: ID of current conversation
        user_id: ID of current user
        memories: Relevant memories
        variables: Context variables
        metadata: Additional context metadata
    """

    conversation_id: str
    user_id: str
    memories: list[AgentMemory] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMetrics:
    """Metrics for agent performance.

    Attributes:
        latency: Processing time in seconds
        token_count: Number of tokens processed
        memory_used: Memory usage in bytes
        error_count: Number of errors encountered
        metadata: Additional metrics
    """

    latency: float
    token_count: int
    memory_used: int
    error_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCapability:
    """Capability offered by an agent.

    Attributes:
        name: Name of the capability
        description: Description of what it does
        parameters: Required parameters
        examples: Usage examples
        metadata: Additional capability metadata
    """

    name: str
    description: str
    parameters: dict[str, Any]
    examples: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentProfile:
    """Profile of an agent's capabilities.

    Attributes:
        agent_id: Unique identifier
        name: Display name
        description: What the agent does
        capabilities: List of capabilities
        metadata: Additional profile metadata
    """

    agent_id: str
    name: str
    description: str
    capabilities: list[AgentCapability]
    metadata: dict[str, Any] = field(default_factory=dict)
