"""OpenAI LLM provider implementation."""

from typing import List, Optional

from pepperpy.llm.providers.base.base import LLMProviderBase
from pepperpy.llm.providers.base.types import (
    ChatMessage,
    CompletionOptions,
    LLMResponse,
    ModelParameters,
)


class OpenAIProvider(LLMProviderBase):
    """Provider implementation for OpenAI LLMs."""

    // ... existing code ...