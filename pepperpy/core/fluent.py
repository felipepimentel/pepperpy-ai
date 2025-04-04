"""
PepperPy Fluent API.

This module defines fluent API classes for declarative workflows in PepperPy.
These classes enable a clean, chainable API for configuring and running tasks.
"""

from pathlib import Path
from typing import Any


class FluentBase:
    """Base class for all fluent API objects."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize fluent object.

        Args:
            name: Object name
            pepper_instance: PepperPy instance
        """
        self.name = name
        self._pepper = pepper_instance
        self._config = {}
        self.result = None
        self.output_path = None

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name='{self.name}')"


class Analysis(FluentBase):
    """Repository analysis configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize analysis.

        Args:
            name: Analysis name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self.enhance = EnhancerProxy(self)

    def prompt(self, text: str) -> "Analysis":
        """Set the analysis prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def output(self, path: str | Path) -> "Analysis":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class EnhancerProxy:
    """Proxy for fluent enhancer configuration."""

    def __init__(self, parent: Any):
        """Initialize enhancer proxy.

        Args:
            parent: Parent object
        """
        self._parent = parent

    def security(self, **options: Any) -> Any:
        """Add security enhancer.

        Args:
            **options: Enhancer options

        Returns:
            Parent object for method chaining
        """
        if "enhancers" not in self._parent._config:
            self._parent._config["enhancers"] = []
        self._parent._config["enhancers"].append(("security", options))
        return self._parent

    def deep_context(self, **options: Any) -> Any:
        """Add deep context enhancer.

        Args:
            **options: Enhancer options

        Returns:
            Parent object for method chaining
        """
        if "enhancers" not in self._parent._config:
            self._parent._config["enhancers"] = []
        self._parent._config["enhancers"].append(("deep_context", options))
        return self._parent

    def best_practices(self, **options: Any) -> Any:
        """Add best practices enhancer.

        Args:
            **options: Enhancer options

        Returns:
            Parent object for method chaining
        """
        if "enhancers" not in self._parent._config:
            self._parent._config["enhancers"] = []
        self._parent._config["enhancers"].append(("best_practices", options))
        return self._parent

    def performance(self, **options: Any) -> Any:
        """Add performance enhancer.

        Args:
            **options: Enhancer options

        Returns:
            Parent object for method chaining
        """
        if "enhancers" not in self._parent._config:
            self._parent._config["enhancers"] = []
        self._parent._config["enhancers"].append(("performance", options))
        return self._parent

    def domain(self, domain: str, **options: Any) -> Any:
        """Add domain-specific enhancer.

        Args:
            domain: Domain name
            **options: Enhancer options

        Returns:
            Parent object for method chaining
        """
        if "enhancers" not in self._parent._config:
            self._parent._config["enhancers"] = []
        options["domain"] = domain
        self._parent._config["enhancers"].append(("domain", options))
        return self._parent


class Processor(FluentBase):
    """Content processor configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize processor.

        Args:
            name: Processor name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)

    def prompt(self, text: str) -> "Processor":
        """Set the processor prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def input(self, content: Any) -> "Processor":
        """Set the input content.

        Args:
            content: Input content

        Returns:
            Self for method chaining
        """
        self._config["input"] = content
        return self

    def parameters(self, params: dict[str, Any]) -> "Processor":
        """Set processing parameters.

        Args:
            params: Parameter dictionary

        Returns:
            Self for method chaining
        """
        self._config["parameters"] = params
        return self

    def output(self, path: str | Path) -> "Processor":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class AgentTask(FluentBase):
    """Agent task configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize agent task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self.enhance = EnhancerProxy(self)

    def prompt(self, text: str) -> "AgentTask":
        """Set the task prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
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

    def output(self, path: str | Path) -> "AgentTask":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class KnowledgeBase(FluentBase):
    """Knowledge base configuration."""

    def add_documents(self, documents: list[str]) -> "KnowledgeBase":
        """Add documents to the knowledge base.

        Args:
            documents: List of documents

        Returns:
            Self for method chaining
        """
        self._config["documents"] = documents
        return self

    def configure(self, **options: Any) -> "KnowledgeBase":
        """Configure knowledge base options.

        Args:
            **options: Configuration options

        Returns:
            Self for method chaining
        """
        self._config.update(options)
        return self


class KnowledgeTask(FluentBase):
    """Knowledge task configuration."""

    def prompt(self, text: str) -> "KnowledgeTask":
        """Set the task prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def using(self, kb: KnowledgeBase) -> "KnowledgeTask":
        """Set the knowledge base to use.

        Args:
            kb: Knowledge base

        Returns:
            Self for method chaining
        """
        self._config["knowledge_base"] = kb
        return self

    def with_history(self, history: list[dict[str, str]]) -> "KnowledgeTask":
        """Set conversation history.

        Args:
            history: Conversation history

        Returns:
            Self for method chaining
        """
        self._config["history"] = history
        return self

    def parameters(self, params: dict[str, Any]) -> "KnowledgeTask":
        """Set task parameters.

        Args:
            params: Parameter dictionary

        Returns:
            Self for method chaining
        """
        self._config["parameters"] = params
        return self

    def output(self, path: str | Path) -> "KnowledgeTask":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class ConversationTask(FluentBase):
    """Conversation task configuration."""

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


class ChatSession(FluentBase):
    """Chat session configuration."""

    def using(self, kb: KnowledgeBase | None = None) -> "ChatSession":
        """Set the knowledge base to use.

        Args:
            kb: Optional knowledge base

        Returns:
            Self for method chaining
        """
        if kb:
            self._config["knowledge_base"] = kb
        return self

    def add_task(self, task: FluentBase) -> "ChatSession":
        """Add a task to the session.

        Args:
            task: Task to add

        Returns:
            Self for method chaining
        """
        if "tasks" not in self._config:
            self._config["tasks"] = []
        self._config["tasks"].append(task)
        return self

    async def start(self) -> None:
        """Start the chat session."""
        raise NotImplementedError("Chat session not yet implemented")
