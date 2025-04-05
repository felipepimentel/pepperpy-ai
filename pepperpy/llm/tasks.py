"""
PepperPy LLM Tasks.

Fluent API for language model task configuration.
"""

from pathlib import Path
from typing import Any

from pepperpy.agent.task import TaskBase


class LLM(TaskBase):
    """Base class for LLM configurations."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize LLM task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["llm_type"] = "text"

    def model(self, model_name: str) -> "LLM":
        """Set the model to use.

        Args:
            model_name: Model identifier

        Returns:
            Self for method chaining
        """
        self._config["model"] = model_name
        return self

    def provider(self, provider_name: str) -> "LLM":
        """Set the provider to use.

        Args:
            provider_name: Provider name

        Returns:
            Self for method chaining
        """
        self._config["provider"] = provider_name
        return self

    def temperature(self, temp: float) -> "LLM":
        """Set the temperature.

        Args:
            temp: Temperature value (0.0-2.0)

        Returns:
            Self for method chaining
        """
        self._config["temperature"] = temp
        return self

    def max_tokens(self, tokens: int) -> "LLM":
        """Set the maximum tokens.

        Args:
            tokens: Maximum token count

        Returns:
            Self for method chaining
        """
        self._config["max_tokens"] = tokens
        return self

    def prompt(self, text: str) -> "LLM":
        """Set the prompt text.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def output(self, path: str | Path) -> "LLM":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class ChatLLM(LLM):
    """Chat model configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize chat LLM task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["llm_type"] = "chat"
        self._config["messages"] = []

    def system(self, message: str) -> "ChatLLM":
        """Add a system message.

        Args:
            message: System message content

        Returns:
            Self for method chaining
        """
        self._config["messages"].append({"role": "system", "content": message})
        return self

    def user(self, message: str) -> "ChatLLM":
        """Add a user message.

        Args:
            message: User message content

        Returns:
            Self for method chaining
        """
        self._config["messages"].append({"role": "user", "content": message})
        return self

    def assistant(self, message: str) -> "ChatLLM":
        """Add an assistant message.

        Args:
            message: Assistant message content

        Returns:
            Self for method chaining
        """
        self._config["messages"].append({"role": "assistant", "content": message})
        return self

    def messages(self, message_list: list[dict[str, str]]) -> "ChatLLM":
        """Set all messages at once.

        Args:
            message_list: List of message dictionaries with role and content

        Returns:
            Self for method chaining
        """
        self._config["messages"] = message_list
        return self


class CompletionLLM(LLM):
    """Text completion model configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize completion LLM task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["llm_type"] = "completion"

    def stop_sequences(self, sequences: list[str]) -> "CompletionLLM":
        """Set stop sequences.

        Args:
            sequences: List of stop sequences

        Returns:
            Self for method chaining
        """
        self._config["stop"] = sequences
        return self

    def top_p(self, value: float) -> "CompletionLLM":
        """Set top_p sampling.

        Args:
            value: Top-p value (0.0-1.0)

        Returns:
            Self for method chaining
        """
        self._config["top_p"] = value
        return self

    def presence_penalty(self, value: float) -> "CompletionLLM":
        """Set presence penalty.

        Args:
            value: Presence penalty value (-2.0 to 2.0)

        Returns:
            Self for method chaining
        """
        self._config["presence_penalty"] = value
        return self

    def frequency_penalty(self, value: float) -> "CompletionLLM":
        """Set frequency penalty.

        Args:
            value: Frequency penalty value (-2.0 to 2.0)

        Returns:
            Self for method chaining
        """
        self._config["frequency_penalty"] = value
        return self
