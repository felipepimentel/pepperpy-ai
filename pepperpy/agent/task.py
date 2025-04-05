"""
PepperPy Agent Task.

Base classes for task configuration.
"""

from pathlib import Path
from typing import Any, Protocol


class Message:
    """Message from an agent."""

    def __init__(self, role: str, content: str):
        """Initialize a message.

        Args:
            role: Message role (system, user, assistant)
            content: Message content
        """
        self.role = role
        self.content = content

    def to_dict(self) -> dict[str, str]:
        """Convert message to dictionary.

        Returns:
            Message as dictionary
        """
        return {"role": self.role, "content": self.content}


class Memory(Protocol):
    """Interface for agent memory."""

    async def add_message(self, message: Message) -> None:
        """Add a message to memory.

        Args:
            message: The message to add.
        """
        ...

    async def get_messages(self) -> list[Message]:
        """Get all messages from memory.

        Returns:
            List of messages.
        """
        ...

    async def clear(self) -> None:
        """Clear all messages from memory."""
        ...


class TaskBase:
    """Base class for all task configurations."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize task base.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        self.name = name
        self._pepper = pepper_instance
        self._config: dict[str, Any] = {"name": name}
        self.output_path: str | Path | None = None

    def execute(self) -> Any:
        """Execute the task.

        Returns:
            Task result
        """
        return self._pepper.execute_task(self)

    def to_config(self) -> dict[str, Any]:
        """Convert task to configuration dictionary.

        Returns:
            Task configuration
        """
        config = self._config.copy()
        if self.output_path:
            config["output_path"] = str(self.output_path)
        return config

    def __str__(self) -> str:
        """String representation of the task."""
        return f"{self.__class__.__name__}(name='{self.name}')"


class EnhancerProxy:
    """Proxy for task enhancement methods."""

    def __init__(self, task: TaskBase):
        """Initialize enhancer proxy.

        Args:
            task: Parent task
        """
        self._task = task

    def with_steps(self, steps: list[dict[str, Any]]) -> TaskBase:
        """Enhance task with predefined steps.

        Args:
            steps: List of step configurations

        Returns:
            Parent task
        """
        self._task._config["steps"] = steps
        return self._task

    def with_context(self, context: dict[str, Any]) -> TaskBase:
        """Enhance task with context information.

        Args:
            context: Context dictionary

        Returns:
            Parent task
        """
        self._task._config["context"] = context
        return self._task

    def with_metadata(self, metadata: dict[str, Any]) -> TaskBase:
        """Enhance task with metadata.

        Args:
            metadata: Metadata dictionary

        Returns:
            Parent task
        """
        self._task._config["metadata"] = metadata
        return self._task

    def with_validation(self, validation_rules: dict[str, Any]) -> TaskBase:
        """Enhance task with validation rules.

        Args:
            validation_rules: Validation rules dictionary

        Returns:
            Parent task
        """
        self._task._config["validation"] = validation_rules
        return self._task


class Agent(Protocol):
    """Interface for an agent."""

    async def initialize(self) -> None:
        """Initialize the agent."""
        ...

    async def execute_task(self, task: str) -> list[Message]:
        """Execute a task and return the messages.

        Args:
            task: The task to execute.

        Returns:
            List of messages from the execution.
        """
        ...


class AgentGroup(Protocol):
    """Interface for a group of agents."""

    async def initialize(self) -> None:
        """Initialize the agent group."""
        ...

    async def execute_task(self, task: str) -> list[Message]:
        """Execute a task using the agent group.

        Args:
            task: The task to execute.

        Returns:
            List of messages from the execution.
        """
        ...


class AgentTask(TaskBase):
    """Agent task configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize agent task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self.enhance = EnhancerProxy(self)
        self._config["agent_type"] = "general"
        self._config["model"] = None

    def prompt(self, text: str) -> "AgentTask":
        """Set the task prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def model(self, model_name: str) -> "AgentTask":
        """Set the model to use.

        Args:
            model_name: Model name

        Returns:
            Self for method chaining
        """
        self._config["model"] = model_name
        return self

    def instruction(self, text: str) -> "AgentTask":
        """Set the instruction text.

        Args:
            text: Instruction text

        Returns:
            Self for method chaining
        """
        self._config["instruction"] = text
        return self

    def context(self, ctx: dict[str, Any]) -> "AgentTask":
        """Set the task context.

        Args:
            ctx: Context dictionary

        Returns:
            Self for method chaining
        """
        self._config["context"] = ctx
        return self

    def capability(self, capability: str) -> "AgentTask":
        """Set the required agent capability.

        Args:
            capability: Capability name

        Returns:
            Self for method chaining
        """
        self._config["capability"] = capability
        return self

    def parameters(self, params: dict[str, Any]) -> "AgentTask":
        """Set task parameters.

        Args:
            params: Parameter dictionary

        Returns:
            Self for method chaining
        """
        self._config["parameters"] = params
        return self

    def format(self, format_type: str) -> "AgentTask":
        """Set the output format.

        Args:
            format_type: Format type

        Returns:
            Self for method chaining
        """
        self._config["format"] = format_type
        return self

    def schema(self, schema_definition: dict[str, Any]) -> "AgentTask":
        """Set the data schema for extraction.

        Args:
            schema_definition: Schema definition

        Returns:
            Self for method chaining
        """
        self._config["schema"] = schema_definition
        return self

    def max_iterations(self, iterations: int) -> "AgentTask":
        """Set the maximum iterations.

        Args:
            iterations: Maximum iterations

        Returns:
            Self for method chaining
        """
        self._config["max_iterations"] = iterations
        return self

    def tools(self, tool_list: list[dict[str, Any]]) -> "AgentTask":
        """Set the available tools.

        Args:
            tool_list: List of tool configurations

        Returns:
            Self for method chaining
        """
        self._config["tools"] = tool_list
        return self

    def output(self, path: str | Path) -> "AgentTask":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class Analysis(AgentTask):
    """Code analysis task configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize analysis task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["agent_type"] = "analysis"
        self._config["analysis_type"] = "general"
        self._config["target"] = None

    def target(self, path: str | Path) -> "Analysis":
        """Set the target path to analyze.

        Args:
            path: Path to analyze

        Returns:
            Self for method chaining
        """
        self._config["target"] = str(path)
        return self

    def language(self, lang: str) -> "Analysis":
        """Set the programming language.

        Args:
            lang: Programming language

        Returns:
            Self for method chaining
        """
        self._config["language"] = lang
        return self

    def analysis_type(self, analysis_type: str) -> "Analysis":
        """Set the analysis type.

        Args:
            analysis_type: Type of analysis

        Returns:
            Self for method chaining
        """
        self._config["analysis_type"] = analysis_type
        return self

    def metrics(self, metrics_list: list[str]) -> "Analysis":
        """Set the metrics to analyze.

        Args:
            metrics_list: List of metrics

        Returns:
            Self for method chaining
        """
        self._config["metrics"] = metrics_list
        return self


class ConversationTask(TaskBase):
    """Conversation task configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize conversation task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self.enhance = EnhancerProxy(self)
        self._config["conversation_type"] = "chat"
        self._config["model"] = None
        self._config["messages"] = []

    def model(self, model_name: str) -> "ConversationTask":
        """Set the model to use.

        Args:
            model_name: Model name

        Returns:
            Self for method chaining
        """
        self._config["model"] = model_name
        return self

    def system(self, content: str) -> "ConversationTask":
        """Add a system message.

        Args:
            content: Message content

        Returns:
            Self for method chaining
        """
        if isinstance(self._config["messages"], list):
            self._config["messages"].append({"role": "system", "content": content})
        return self

    def user(self, content: str) -> "ConversationTask":
        """Add a user message.

        Args:
            content: Message content

        Returns:
            Self for method chaining
        """
        if isinstance(self._config["messages"], list):
            self._config["messages"].append({"role": "user", "content": content})
        return self

    def assistant(self, content: str) -> "ConversationTask":
        """Add an assistant message.

        Args:
            content: Message content

        Returns:
            Self for method chaining
        """
        if isinstance(self._config["messages"], list):
            self._config["messages"].append({"role": "assistant", "content": content})
        return self

    def prompt(self, text: str) -> "ConversationTask":
        """Set the task prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def history(self, history: list[dict[str, str]]) -> "ConversationTask":
        """Set conversation history.

        Args:
            history: Conversation history

        Returns:
            Self for method chaining
        """
        self._config["history"] = history
        return self

    def messages(self, message_list: list[dict[str, str]]) -> "ConversationTask":
        """Set the message history.

        Args:
            message_list: List of message dictionaries

        Returns:
            Self for method chaining
        """
        self._config["messages"] = message_list
        return self

    def conversation_id(self, id_str: str) -> "ConversationTask":
        """Set conversation ID.

        Args:
            id_str: Conversation ID

        Returns:
            Self for method chaining
        """
        self._config["conversation_id"] = id_str
        return self

    def output(self, path: str | Path) -> "ConversationTask":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class ChatSession(ConversationTask):
    """Chat session configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize chat session.

        Args:
            name: Session name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["conversation_type"] = "chat_session"
        self._config["memory"] = True
        self._config["memory_window"] = 10
        self._tasks: list[TaskBase] = []

    def with_memory(self, enable: bool = True) -> "ChatSession":
        """Enable or disable chat memory.

        Args:
            enable: Whether to enable memory

        Returns:
            Self for method chaining
        """
        self._config["memory"] = enable
        return self

    def memory_window(self, messages: int) -> "ChatSession":
        """Set the memory window size.

        Args:
            messages: Number of messages to remember

        Returns:
            Self for method chaining
        """
        self._config["memory_window"] = messages
        return self

    def add_task(self, task: TaskBase) -> "ChatSession":
        """Add a task to the session.

        Args:
            task: Task to add

        Returns:
            Self for method chaining
        """
        self._tasks.append(task)
        return self

    async def start(self) -> None:
        """Start the chat session."""
        if not self._tasks:
            raise ValueError("No tasks added to the chat session")

        # Implementation would be handled by the PepperPy instance
