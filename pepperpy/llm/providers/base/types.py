"""Type definitions for LLM providers.

This module defines the types used by LLM providers.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union


class MessageRole(str, Enum):
    """Role of a chat message."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """Chat message for LLM providers."""

    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class CompletionOptions:
    """Options for text completion."""

    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    text: str
    model: str
    finish_reason: Optional[str] = None
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelParameters:
    """Parameters for LLM models."""

    model: str
    context_window: int
    max_output_tokens: int
    supports_functions: bool = False
    supports_vision: bool = False
    additional_capabilities: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(Protocol):
    """Protocol defining the interface for LLM providers."""

    def generate(
        self,
        prompt: str,
        options: Optional[CompletionOptions] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate text completion."""
        ...

    def chat(
        self,
        messages: List[ChatMessage],
        options: Optional[CompletionOptions] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate chat completion."""
        ...

    def get_models(self) -> List[str]:
        """Get list of available models."""
        ...

    def get_model_parameters(self, model_name: str) -> ModelParameters:
        """Get parameters for a specific model."""
        ...
