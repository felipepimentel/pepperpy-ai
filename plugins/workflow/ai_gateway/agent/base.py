"""Core interfaces and factories for the Agentic AI capability.

This module defines the base interfaces and factories for creating and managing
agentic AI components within the AI Gateway.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any, Protocol, TypeVar

logger = logging.getLogger(__name__)

# Type definitions
AgentId = str
TaskId = str
T = TypeVar("T")
ModelProvider = Any  # Placeholder for actual model provider type


class DecisionStrategy(Enum):
    """Strategy used for agent decision making."""

    RULE_BASED = "rule_based"
    UTILITY_BASED = "utility_based"
    GOAL_ORIENTED = "goal_oriented"
    MULTI_MODEL_CONSENSUS = "multi_model_consensus"


class AgentCapability(Enum):
    """Capabilities that an agent can possess."""

    TEXT_PROCESSING = "text_processing"
    TASK_PLANNING = "task_planning"
    DECISION_MAKING = "decision_making"
    DATABASE_INTEGRATION = "database_integration"
    TOOL_USAGE = "tool_usage"
    MEMORY_MANAGEMENT = "memory_management"
    LEARNING = "learning"
    COLLABORATION = "collaboration"
    MULTIMODAL = "multimodal"
    CHAT = "chat"
    RAG = "rag"
    FUNCTION_CALLING = "function_calling"
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    IMAGE_GENERATION = "image_generation"
    IMAGE_ANALYSIS = "image_analysis"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    AUDIO_GENERATION = "audio_generation"
    PLANNING = "planning"
    REASONING = "reasoning"
    SEARCH = "search"
    MATH = "math"
    DATA_ANALYSIS = "data_analysis"


class AgentRole(Enum):
    """Role that an agent can fulfill."""

    COORDINATOR = auto()
    SPECIALIST = auto()
    EXECUTOR = auto()
    VALIDATOR = auto()
    MONITOR = auto()
    USER_INTERFACE = auto()


class AgentStatus(Enum):
    """Status of an agent."""

    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    PAUSED = "paused"
    TERMINATED = "terminated"


@dataclass
class AgentMetrics:
    """Metrics tracked for an agent."""

    total_tasks_completed: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_task_duration_ms: float = 0.0
    total_tokens_used: int = 0
    last_active: datetime | None = None
    feedback_score: float = 0.0


@dataclass
class AgentContext:
    """Context in which an agent operates."""

    session_id: str
    user_id: str | None = None
    environment_variables: dict[str, str] = None
    metadata: dict[str, Any] = None


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    name: str
    capabilities: list[AgentCapability]
    role: AgentRole
    decision_strategy: DecisionStrategy
    model_providers: list[str]
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout_seconds: int = 30
    retry_attempts: int = 3
    tools: list[str] = None
    memory_limit: int = 10
    custom_settings: dict[str, Any] = None


class TaskStatus(Enum):
    """Status of a task."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Priority of a task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task:
    """Task for an agent to execute."""

    def __init__(
        self,
        id: Optional[str] = None,
        objective: str = "",
        parameters: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        agent_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
    ):
        """Initialize a task.

        Args:
            id: Task ID (generated if not provided)
            objective: Task objective
            parameters: Task parameters
            priority: Task priority
            agent_id: ID of agent assigned to this task
            conversation_id: ID of conversation this task is part of
            metadata: Additional metadata
        """
        self.id = id or str(uuid.uuid4())
        self.objective = objective
        self.parameters = parameters or {}
        self.priority = priority
        self.agent_id = agent_id
        self.conversation_id = conversation_id
        self.metadata = metadata or {}

        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.assigned_at: Optional[datetime] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "objective": self.objective,
            "parameters": self.parameters,
            "priority": self.priority.value,
            "agent_id": self.agent_id,
            "conversation_id": self.conversation_id,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "result": self.result,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Task
        """
        task = cls(
            id=data["id"],
            objective=data["objective"],
            parameters=data.get("parameters", {}),
            priority=TaskPriority(data.get("priority", "medium")),
            agent_id=data.get("agent_id"),
            conversation_id=data.get("conversation_id"),
            metadata=data.get("metadata", {}),
        )

        task.status = TaskStatus(data.get("status", "pending"))

        if data.get("created_at"):
            task.created_at = datetime.fromisoformat(data["created_at"])

        if data.get("assigned_at"):
            task.assigned_at = datetime.fromisoformat(data["assigned_at"])

        if data.get("started_at"):
            task.started_at = datetime.fromisoformat(data["started_at"])

        if data.get("completed_at"):
            task.completed_at = datetime.fromisoformat(data["completed_at"])

        task.result = data.get("result")
        task.error = data.get("error")

        return task


class TaskResult(Protocol):
    """Protocol for task results."""

    success: bool
    output: Any
    error: str | None
    metrics: dict[str, Any]


class AgentMemory(Protocol):
    """Memory for an agent."""

    async def add(self, key: str, value: Any) -> None:
        """Add an item to memory."""
        ...

    async def get(self, key: str) -> Any | None:
        """Retrieve an item from memory."""
        ...

    async def update(self, key: str, value: Any) -> None:
        """Update an item in memory."""
        ...

    async def remove(self, key: str) -> None:
        """Remove an item from memory."""
        ...

    async def clear(self) -> None:
        """Clear all memory."""
        ...


class AgentTool(Protocol):
    """Tool that an agent can use."""

    name: str
    description: str

    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        ...


class Agent(Protocol):
    """Protocol for an agent."""

    agent_id: AgentId
    config: AgentConfig
    status: AgentStatus
    context: AgentContext
    metrics: AgentMetrics
    memory: AgentMemory

    async def initialize(self) -> None:
        """Initialize the agent."""
        ...

    async def process_instruction(self, instruction: str) -> Any:
        """Process a user instruction."""
        ...

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a task."""
        ...

    async def plan_tasks(self, objective: str) -> list[Task]:
        """Plan tasks to achieve an objective."""
        ...

    async def collaborate(self, agent_id: AgentId, message: Any) -> Any:
        """Collaborate with another agent."""
        ...

    async def learn_from_feedback(self, feedback: Any) -> None:
        """Learn from user feedback."""
        ...

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        ...


class AgentSystem(Protocol):
    """Protocol for an agent system."""

    agents: dict[AgentId, Agent]

    async def create_agent(self, config: AgentConfig, context: AgentContext) -> Agent:
        """Create a new agent."""
        ...

    async def get_agent(self, agent_id: AgentId) -> Agent | None:
        """Get an agent by ID."""
        ...

    async def remove_agent(self, agent_id: AgentId) -> None:
        """Remove an agent."""
        ...

    async def process_instruction(self, instruction: str, context: AgentContext) -> Any:
        """Process a user instruction using the appropriate agents."""
        ...

    async def execute_workflow(self, tasks: list[Task]) -> dict[TaskId, Any]:
        """Execute a workflow consisting of multiple tasks."""
        ...

    async def monitor_performance(self) -> dict[AgentId, AgentMetrics]:
        """Monitor the performance of all agents."""
        ...


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        role: AgentRole,
        capabilities: list[AgentCapability],
        config: dict[str, Any],
    ):
        """Initialize base agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Description of the agent
            role: Role of the agent
            capabilities: Capabilities of the agent
            config: Configuration for the agent
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.role = role
        self.capabilities = capabilities
        self.config = config
        self.created_at = datetime.now()
        self.task_history: list[str] = []  # IDs of tasks
        self.current_task: Task | None = None
        self.status = "idle"

    @abstractmethod
    async def execute(self, task: Task, context: AgentContext) -> Any:
        """Execute a task.

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Result of task execution
        """
        pass

    def can_handle_task(self, task: Task) -> bool:
        """Check if this agent can handle a task.

        Args:
            task: Task to check

        Returns:
            True if the agent can handle the task, False otherwise
        """
        # Check if agent has all required capabilities
        return all(cap in self.capabilities for cap in task.required_capabilities)

    def to_dict(self) -> dict[str, Any]:
        """Convert agent to dictionary.

        Returns:
            Dictionary representation of agent
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "role": self.role.name,
            "capabilities": [cap.name for cap in self.capabilities],
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "task_history": self.task_history,
            "current_task": self.current_task.id if self.current_task else None,
        }


class ModelBasedAgent(BaseAgent):
    """Agent that uses a language model to execute tasks."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        role: AgentRole,
        capabilities: list[AgentCapability],
        config: dict[str, Any],
        model_provider: Any,
        system_prompt: str,
        memory_size: int = 10,
    ):
        """Initialize model-based agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Description of the agent
            role: Role of the agent
            capabilities: Capabilities of the agent
            config: Configuration for the agent
            model_provider: Provider for language model
            system_prompt: System prompt for the model
            memory_size: Number of previous interactions to remember
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            role=role,
            capabilities=capabilities,
            config=config,
        )
        self.model_provider = model_provider
        self.system_prompt = system_prompt
        self.memory_size = memory_size
        self.conversation_history: list[dict[str, str]] = []

    async def execute(self, task: Task, context: AgentContext) -> Any:
        """Execute a task using the language model.

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Result of task execution
        """
        self.current_task = task
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        try:
            # Log the task start
            context.add_to_history({
                "agent_id": self.agent_id,
                "task_id": task.id,
                "event": "task_started",
                "task_objective": task.objective,
            })

            # Create the prompt for this task
            messages = self._create_messages_for_task(task, context)

            # Execute the model call
            logger.info(f"Agent {self.name} executing task: {task.objective}")
            response = await self.model_provider.chat(messages=messages)

            # Process the result
            result = self._process_model_response(response, task, context)

            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            # Log the completion
            context.add_to_history({
                "agent_id": self.agent_id,
                "task_id": task.id,
                "event": "task_completed",
                "result_summary": str(result)[:100]
                + ("..." if len(str(result)) > 100 else ""),
            })

            # Add to task history
            self.task_history.append(task.id)

            return result

        except Exception as e:
            logger.exception(
                f"Agent {self.name} failed to execute task: {task.objective}"
            )

            # Update task status
            task.status = TaskStatus.FAILED
            task.error = str(e)

            # Log the failure
            context.add_to_history({
                "agent_id": self.agent_id,
                "task_id": task.id,
                "event": "task_failed",
                "error": str(e),
            })

            raise

        finally:
            self.current_task = None

    def _create_messages_for_task(
        self, task: Task, context: AgentContext
    ) -> list[dict[str, str]]:
        """Create messages for the model based on the task.

        Args:
            task: Task to create messages for
            context: Execution context

        Returns:
            List of messages for the model
        """
        # Start with system prompt
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history
        messages.extend(self.conversation_history[-self.memory_size :])

        # Create the user message for this task
        task_message = (
            f"Task Objective: {task.objective}\n\n"
            f"Task Parameters: {task.parameters}\n\n"
        )

        # Add information about available tools if any
        available_tools = context.get_available_tools()
        if available_tools:
            task_message += f"Available Tools: {', '.join(available_tools)}\n\n"

        # Add information about shared memory if relevant
        if task.parameters.get("use_shared_memory", False):
            task_message += "Shared Memory Contents:\n"
            task_message += str(context.shared_memory)
            task_message += "\n\n"

        messages.append({"role": "user", "content": task_message})

        return messages

    def _process_model_response(
        self, response: dict[str, Any], task: Task, context: AgentContext
    ) -> Any:
        """Process the response from the model.

        Args:
            response: Response from the model
            task: The task being executed
            context: Execution context

        Returns:
            Processed result
        """
        # Extract the model's response content
        content = response.get("content", "")

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": task.objective})
        self.conversation_history.append({"role": "assistant", "content": content})

        # Process based on task type or parameters
        if task.parameters.get("output_format") == "json":
            # Attempt to extract JSON from the response
            import json
            import re

            # Look for JSON pattern
            json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from response")

            # Try to find any JSON-like content
            json_like_match = re.search(r"({.*})", content, re.DOTALL)
            if json_like_match:
                json_str = json_like_match.group(1)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from response")

            logger.warning("Expected JSON output but none found in response")

        # Default: return the raw content
        return content


class RuleBasedAgent(BaseAgent):
    """Agent that uses predefined rules to execute tasks."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        role: AgentRole,
        capabilities: list[AgentCapability],
        config: dict[str, Any],
        rules: dict[str, Any],
    ):
        """Initialize rule-based agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Description of the agent
            role: Role of the agent
            capabilities: Capabilities of the agent
            config: Configuration for the agent
            rules: Rules for the agent
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            role=role,
            capabilities=capabilities,
            config=config,
        )
        self.rules = rules

    async def execute(self, task: Task, context: AgentContext) -> Any:
        """Execute a task using predefined rules.

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Result of task execution
        """
        self.current_task = task
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        try:
            # Log the task start
            context.add_to_history({
                "agent_id": self.agent_id,
                "task_id": task.id,
                "event": "task_started",
                "task_objective": task.objective,
            })

            # Find applicable rules
            applicable_rules = self._find_applicable_rules(task)

            if not applicable_rules:
                raise ValueError(
                    f"No applicable rules found for task: {task.objective}"
                )

            # Execute the rules
            logger.info(
                f"Agent {self.name} executing task with {len(applicable_rules)} rules: {task.objective}"
            )
            result = await self._apply_rules(applicable_rules, task, context)

            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            # Log the completion
            context.add_to_history({
                "agent_id": self.agent_id,
                "task_id": task.id,
                "event": "task_completed",
                "result_summary": str(result)[:100]
                + ("..." if len(str(result)) > 100 else ""),
                "applied_rules": [rule["name"] for rule in applicable_rules],
            })

            # Add to task history
            self.task_history.append(task.id)

            return result

        except Exception as e:
            logger.exception(
                f"Agent {self.name} failed to execute task: {task.objective}"
            )

            # Update task status
            task.status = TaskStatus.FAILED
            task.error = str(e)

            # Log the failure
            context.add_to_history({
                "agent_id": self.agent_id,
                "task_id": task.id,
                "event": "task_failed",
                "error": str(e),
            })

            raise

        finally:
            self.current_task = None

    def _find_applicable_rules(self, task: Task) -> list[dict[str, Any]]:
        """Find rules applicable to a task.

        Args:
            task: Task to find rules for

        Returns:
            List of applicable rules
        """
        applicable_rules = []

        for rule in self.rules.get("rules", []):
            # Check if rule applies to this task
            if "task_pattern" in rule:
                import re

                if not re.search(rule["task_pattern"], task.objective, re.IGNORECASE):
                    continue

            # Check if required parameters are present
            if "required_parameters" in rule:
                if not all(
                    param in task.parameters for param in rule["required_parameters"]
                ):
                    continue

            # Rule is applicable
            applicable_rules.append(rule)

        return applicable_rules

    async def _apply_rules(
        self, rules: list[dict[str, Any]], task: Task, context: AgentContext
    ) -> Any:
        """Apply rules to execute a task.

        Args:
            rules: Rules to apply
            task: Task to execute
            context: Execution context

        Returns:
            Result of applying the rules
        """
        result = None

        # Sort rules by priority if specified
        sorted_rules = sorted(rules, key=lambda r: r.get("priority", 0), reverse=True)

        for rule in sorted_rules:
            rule_name = rule.get("name", "unnamed")
            logger.debug(f"Applying rule: {rule_name}")

            # Apply transformations if specified
            if "transformations" in rule:
                for transform in rule["transformations"]:
                    if transform["type"] == "extract":
                        # Extract data using regex or path
                        if "regex" in transform:
                            import re

                            source = transform.get("source", "objective")
                            source_text = (
                                task.objective
                                if source == "objective"
                                else task.parameters.get(source, "")
                            )
                            match = re.search(transform["regex"], source_text)
                            if match:
                                extracted = match.group(transform.get("group", 0))
                                task.parameters[transform["target"]] = extracted

                    elif transform["type"] == "calculate":
                        # Perform calculation
                        if "expression" in transform:
                            import ast
                            import operator

                            # Define safe operators
                            operators = {
                                ast.Add: operator.add,
                                ast.Sub: operator.sub,
                                ast.Mult: operator.mul,
                                ast.Div: operator.truediv,
                                ast.Mod: operator.mod,
                                ast.Pow: operator.pow,
                            }

                            # Build variable context from parameters
                            eval_context = {**task.parameters}

                            # Evaluate expression safely
                            def eval_expr(node):
                                if isinstance(node, ast.Num):
                                    return node.n
                                elif isinstance(node, ast.BinOp):
                                    return operators[type(node.op)](
                                        eval_expr(node.left), eval_expr(node.right)
                                    )
                                elif isinstance(node, ast.Name):
                                    if node.id in eval_context:
                                        return eval_context[node.id]
                                    raise ValueError(f"Variable not found: {node.id}")
                                else:
                                    raise ValueError(f"Unsupported operation: {node}")

                            try:
                                expr = ast.parse(
                                    transform["expression"], mode="eval"
                                ).body
                                result = eval_expr(expr)
                                task.parameters[transform["target"]] = result
                            except Exception as e:
                                logger.error(f"Error evaluating expression: {e}")

            # Execute actions if specified
            if "actions" in rule:
                for action in rule["actions"]:
                    if action["type"] == "tool":
                        # Execute tool
                        tool_name = action["tool"]
                        tool_params = {}

                        # Map parameters
                        if "parameter_mapping" in action:
                            for tool_param, task_param in action[
                                "parameter_mapping"
                            ].items():
                                if task_param in task.parameters:
                                    tool_params[tool_param] = task.parameters[
                                        task_param
                                    ]

                        # Execute tool
                        try:
                            tool = context.get_tool(tool_name)
                            tool_result = await tool(**tool_params)

                            # Store result if target specified
                            if "result_target" in action:
                                task.parameters[action["result_target"]] = tool_result

                            # Update result
                            result = tool_result

                        except Exception as e:
                            logger.error(f"Error executing tool {tool_name}: {e}")
                            if action.get("required", False):
                                raise

                    elif action["type"] == "return":
                        # Return a value
                        if "value" in action:
                            result = action["value"]
                        elif (
                            "parameter" in action
                            and action["parameter"] in task.parameters
                        ):
                            result = task.parameters[action["parameter"]]

                        # If final is True, return immediately
                        if action.get("final", False):
                            return result

        return result


class CompositeAgent(BaseAgent):
    """Agent that combines multiple sub-agents to execute tasks."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        role: AgentRole,
        capabilities: list[AgentCapability],
        config: dict[str, Any],
        sub_agents: list[BaseAgent],
        coordinator: BaseAgent | None = None,
    ):
        """Initialize composite agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Description of the agent
            role: Role of the agent
            capabilities: Capabilities of the agent
            config: Configuration for the agent
            sub_agents: List of sub-agents
            coordinator: Optional coordinator agent
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            role=role,
            capabilities=capabilities,
            config=config,
        )
        self.sub_agents = sub_agents
        self.coordinator = coordinator

    async def execute(self, task: Task, context: AgentContext) -> Any:
        """Execute a task by coordinating sub-agents.

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Result of task execution
        """
        self.current_task = task
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        try:
            # Log the task start
            context.add_to_history({
                "agent_id": self.agent_id,
                "task_id": task.id,
                "event": "task_started",
                "task_objective": task.objective,
            })

            # If we have a coordinator, use it to plan the execution
            if self.coordinator:
                planning_task = Task(
                    objective=f"Plan execution of: {task.objective}",
                    parameters={
                        "original_task": task.to_dict(),
                        "available_agents": [
                            {
                                "agent_id": agent.agent_id,
                                "name": agent.name,
                                "capabilities": [
                                    cap.name for cap in agent.capabilities
                                ],
                            }
                            for agent in self.sub_agents
                        ],
                    },
                )

                logger.info(
                    f"Composite agent {self.name} planning task: {task.objective}"
                )
                plan = await self.coordinator.execute(planning_task, context)

                # Execute the plan
                result = await self._execute_plan(plan, task, context)
            else:
                # No coordinator, assign to the most capable agent
                capable_agents = [
                    agent for agent in self.sub_agents if agent.can_handle_task(task)
                ]

                if not capable_agents:
                    raise ValueError(f"No sub-agent can handle task: {task.objective}")

                # Select the agent (could use more sophisticated selection)
                selected_agent = capable_agents[0]

                # Execute with the selected agent
                logger.info(
                    f"Composite agent {self.name} delegating to: {selected_agent.name}"
                )
                result = await selected_agent.execute(task, context)

            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            # Log the completion
            context.add_to_history({
                "agent_id": self.agent_id,
                "task_id": task.id,
                "event": "task_completed",
                "result_summary": str(result)[:100]
                + ("..." if len(str(result)) > 100 else ""),
            })

            # Add to task history
            self.task_history.append(task.id)

            return result

        except Exception as e:
            logger.exception(
                f"Composite agent {self.name} failed to execute task: {task.objective}"
            )

            # Update task status
            task.status = TaskStatus.FAILED
            task.error = str(e)

            # Log the failure
            context.add_to_history({
                "agent_id": self.agent_id,
                "task_id": task.id,
                "event": "task_failed",
                "error": str(e),
            })

            raise

        finally:
            self.current_task = None

    async def _execute_plan(
        self, plan: dict[str, Any], original_task: Task, context: AgentContext
    ) -> Any:
        """Execute a plan created by the coordinator.

        Args:
            plan: Plan created by coordinator
            original_task: Original task
            context: Execution context

        Returns:
            Result of plan execution
        """
        # Extract steps from the plan
        steps = plan.get("steps", [])

        if not steps:
            raise ValueError("Plan contains no steps")

        logger.info(f"Executing plan with {len(steps)} steps")

        # Track results of each step
        step_results = {}
        final_result = None

        # Execute each step in sequence
        for i, step in enumerate(steps):
            step_id = step.get("id", f"step_{i + 1}")
            agent_id = step.get("agent_id")
            objective = step.get("objective", f"Step {i + 1}")
            parameters = step.get("parameters", {})

            # Find the agent
            agent = next(
                (a for a in self.sub_agents if a.agent_id == agent_id),
                None,
            )

            if not agent:
                raise ValueError(f"Agent not found for step {step_id}: {agent_id}")

            # Create step task
            step_task = Task(
                objective=objective,
                parameters={
                    **parameters,
                    "original_task": original_task.to_dict(),
                    "step_results": step_results,
                    "step_id": step_id,
                },
                parent_id=original_task.id,
            )

            # Execute step
            logger.info(f"Executing step {step_id} with agent {agent.name}")
            step_result = await agent.execute(step_task, context)

            # Store result
            step_results[step_id] = step_result

            # If this is the last step or marked as final, use as final result
            if i == len(steps) - 1 or step.get("final", False):
                final_result = step_result

        return final_result


class AgentFactory:
    """Factory for creating agents."""

    @staticmethod
    async def create_agent(
        agent_type: str,
        agent_config: dict[str, Any],
        context: AgentContext | None = None,
    ) -> BaseAgent:
        """Create an agent based on configuration.

        Args:
            agent_type: Type of agent to create
            agent_config: Configuration for the agent
            context: Optional agent context

        Returns:
            Created agent

        Raises:
            ValueError: If agent type is unknown
        """
        agent_id = agent_config.get("agent_id", str(uuid.uuid4()))
        name = agent_config.get("name", f"{agent_type}_agent")
        description = agent_config.get("description", f"{agent_type} agent")
        role_name = agent_config.get("role", "ASSISTANT")
        role = AgentRole[role_name] if isinstance(role_name, str) else role_name

        # Parse capabilities
        capabilities = []
        for cap_name in agent_config.get("capabilities", []):
            try:
                capabilities.append(
                    AgentCapability[cap_name] if isinstance(cap_name, str) else cap_name
                )
            except KeyError:
                logger.warning(f"Unknown capability: {cap_name}")

        if agent_type == "model":
            from ..models import get_model_provider

            model_name = agent_config.get("model", "default")
            model_provider = await get_model_provider(model_name)

            system_prompt = agent_config.get(
                "system_prompt", "You are a helpful assistant."
            )
            memory_size = agent_config.get("memory_size", 10)

            return ModelBasedAgent(
                agent_id=agent_id,
                name=name,
                description=description,
                role=role,
                capabilities=capabilities,
                config=agent_config,
                model_provider=model_provider,
                system_prompt=system_prompt,
                memory_size=memory_size,
            )

        elif agent_type == "rule":
            rules = agent_config.get("rules", {"rules": []})

            return RuleBasedAgent(
                agent_id=agent_id,
                name=name,
                description=description,
                role=role,
                capabilities=capabilities,
                config=agent_config,
                rules=rules,
            )

        elif agent_type == "composite":
            # Create sub-agents
            sub_agents = []
            for sub_config in agent_config.get("sub_agents", []):
                sub_type = sub_config.get("type", "model")
                sub_agent = await AgentFactory.create_agent(
                    sub_type, sub_config, context
                )
                sub_agents.append(sub_agent)

            # Create coordinator if specified
            coordinator = None
            if "coordinator" in agent_config:
                coord_type = agent_config["coordinator"].get("type", "model")
                coordinator = await AgentFactory.create_agent(
                    coord_type, agent_config["coordinator"], context
                )

            return CompositeAgent(
                agent_id=agent_id,
                name=name,
                description=description,
                role=role,
                capabilities=capabilities,
                config=agent_config,
                sub_agents=sub_agents,
                coordinator=coordinator,
            )

        else:
            raise ValueError(f"Unknown agent type: {agent_type}")


class BaseAgentSystem:
    """Base implementation of an agent system."""

    def __init__(self):
        """Initialize an agent system."""
        self.agents: dict[AgentId, Agent] = {}
        self._agent_constructors: dict[str, type[Agent]] = {}
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the agent system."""
        if self._initialized:
            return

        try:
            # Register agent implementations
            self._register_agent_implementations()

            self._initialized = True
            logger.info("Agent system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent system: {e}")
            raise

    async def create_agent(
        self, config: AgentConfig, context: AgentContext, agent_type: str = "default"
    ) -> Agent:
        """Create a new agent.

        Args:
            config: Configuration for the agent
            context: Context in which the agent operates
            agent_type: Type of agent to create

        Returns:
            Created agent
        """
        if not self._initialized:
            await self.initialize()

        async with self._lock:
            agent_id = f"{config.name}_{len(self.agents) + 1}"

            # Create memory for the agent
            memory = await self._create_memory()

            # Create tools for the agent
            tools = await self._create_tools(config.tools or [])

            # Create model providers for the agent
            model_providers = await self._create_model_providers(config.model_providers)

            # Create the agent
            agent_constructor = self._agent_constructors.get(agent_type)
            if not agent_constructor:
                raise ValueError(f"Unknown agent type: {agent_type}")

            agent = agent_constructor(
                agent_id=agent_id,
                config=config,
                context=context,
                memory=memory,
                tools=tools,
                model_providers=model_providers,
            )

            # Initialize the agent
            await agent.initialize()

            # Store the agent
            self.agents[agent_id] = agent

            return agent

    async def get_agent(self, agent_id: AgentId) -> Agent | None:
        """Get an agent by ID.

        Args:
            agent_id: ID of the agent to get

        Returns:
            Agent with the given ID, or None if not found
        """
        return self.agents.get(agent_id)

    async def remove_agent(self, agent_id: AgentId) -> None:
        """Remove an agent.

        Args:
            agent_id: ID of the agent to remove
        """
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            await agent.cleanup()
            del self.agents[agent_id]

    async def process_instruction(
        self, instruction: str, context: AgentContext, agent_id: AgentId | None = None
    ) -> Any:
        """Process a user instruction using the appropriate agents.

        Args:
            instruction: User instruction to process
            context: Context for processing the instruction
            agent_id: ID of the agent to use, or None to select automatically

        Returns:
            Result of processing the instruction
        """
        if not self._initialized:
            await self.initialize()

        if agent_id:
            # Use the specified agent
            agent = await self.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent not found: {agent_id}")
            return await agent.process_instruction(instruction)
        else:
            # Select the appropriate agent based on the instruction
            agent = await self._select_agent(instruction, context)
            return await agent.process_instruction(instruction)

    async def execute_workflow(
        self, tasks: list[Task], context: AgentContext | None = None
    ) -> dict[TaskId, Any]:
        """Execute a workflow consisting of multiple tasks.

        Args:
            tasks: Tasks to execute
            context: Context for executing the workflow

        Returns:
            Results of executing the tasks
        """
        if not self._initialized:
            await self.initialize()

        results: dict[TaskId, Any] = {}

        # Build dependency graph
        dependency_graph: dict[TaskId, set[TaskId]] = {}
        for task in tasks:
            dependency_graph[task.task_id] = set(task.dependencies or [])

        # Execute tasks in dependency order
        remaining_tasks = set(task.task_id for task in tasks)
        task_map = {task.task_id: task for task in tasks}

        while remaining_tasks:
            # Find tasks with no dependencies or all dependencies satisfied
            executable_tasks = [
                task_id
                for task_id in remaining_tasks
                if not dependency_graph[task_id]
                or all(
                    dep_id not in remaining_tasks
                    for dep_id in dependency_graph[task_id]
                )
            ]

            if not executable_tasks:
                # Circular dependency or other issue
                raise ValueError("Unable to resolve task dependencies")

            # Execute the tasks
            for task_id in executable_tasks:
                task = task_map[task_id]

                # Assign to an agent if not already assigned
                if not task.assigned_to:
                    agent = await self._select_agent_for_task(task, context)
                    task.assigned_to = agent.agent_id
                else:
                    agent = await self.get_agent(task.assigned_to)
                    if not agent:
                        raise ValueError(
                            f"Assigned agent not found: {task.assigned_to}"
                        )

                # Execute the task
                result = await agent.execute_task(task)
                results[task_id] = result

                # Remove from remaining tasks
                remaining_tasks.remove(task_id)

        return results

    async def monitor_performance(self) -> dict[AgentId, AgentMetrics]:
        """Monitor the performance of all agents.

        Returns:
            Performance metrics for all agents
        """
        return {agent_id: agent.metrics for agent_id, agent in self.agents.items()}

    async def cleanup(self) -> None:
        """Clean up agent system resources."""
        if not self._initialized:
            return

        try:
            # Clean up all agents
            for agent_id in list(self.agents.keys()):
                await self.remove_agent(agent_id)

            self._initialized = False
            logger.info("Agent system cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up agent system: {e}")
            raise

    def _register_agent_implementations(self) -> None:
        """Register agent implementations."""
        # This is a placeholder for actual implementation
        # In a real implementation, this would dynamically discover and register
        # agent implementations, either through a plugin system or by scanning
        # a directory for agent implementations.
        pass

    async def _create_memory(self) -> AgentMemory:
        """Create memory for an agent.

        Returns:
            Memory for the agent
        """
        # This is a placeholder for actual implementation
        from .memory import SimpleMemory

        return SimpleMemory()

    async def _create_tools(self, tool_names: list[str]) -> dict[str, AgentTool]:
        """Create tools for an agent.

        Args:
            tool_names: Names of tools to create

        Returns:
            Tools for the agent
        """
        # This is a placeholder for actual implementation
        return {}

    async def _create_model_providers(
        self, provider_names: list[str]
    ) -> dict[str, ModelProvider]:
        """Create model providers for an agent.

        Args:
            provider_names: Names of providers to create

        Returns:
            Model providers for the agent
        """
        # This is a placeholder for actual implementation
        return {}

    async def _select_agent(self, instruction: str, context: AgentContext) -> Agent:
        """Select an agent based on an instruction and context.

        Args:
            instruction: User instruction
            context: Context for the instruction

        Returns:
            Selected agent
        """
        # This is a placeholder for actual implementation
        # In a real implementation, this would use NLP or another technique to
        # determine the most appropriate agent for the instruction.

        # For now, just use the first agent or create a new one if none exist
        if not self.agents:
            # Create a default agent
            config = AgentConfig(
                name="default",
                capabilities=[AgentCapability.TEXT_PROCESSING],
                role=AgentRole.EXECUTOR,
                decision_strategy=DecisionStrategy.RULE_BASED,
                model_providers=["default"],
            )
            return await self.create_agent(config, context)

        return next(iter(self.agents.values()))

    async def _select_agent_for_task(
        self, task: Task, context: AgentContext | None
    ) -> Agent:
        """Select an agent for a task.

        Args:
            task: Task to select an agent for
            context: Context for the task

        Returns:
            Selected agent
        """
        # This is a placeholder for actual implementation
        return await self._select_agent(
            task.description, context or AgentContext(session_id="default")
        )


def create_agent_system() -> BaseAgentSystem:
    """Create an agent system.

    Returns:
        Created agent system
    """
    return BaseAgentSystem()


async def process_instruction(
    instruction: str, session_id: str, user_id: str | None = None
) -> Any:
    """Process a user instruction.

    Args:
        instruction: User instruction to process
        session_id: Session ID
        user_id: User ID

    Returns:
        Result of processing the instruction
    """
    # Create agent system
    agent_system = create_agent_system()
    await agent_system.initialize()

    try:
        # Create context
        context = AgentContext(session_id=session_id, user_id=user_id)

        # Process instruction
        return await agent_system.process_instruction(instruction, context)
    finally:
        # Clean up
        await agent_system.cleanup()
