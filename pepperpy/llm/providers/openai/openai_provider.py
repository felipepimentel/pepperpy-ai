"""OpenAI LLM provider implementation."""

from typing import List, Optional

from pepperpy.llm.providers.base.base import LLMProviderBase

    ChatMessage,
    CompletionOptions,
    LLMResponse,
    ModelParameters,
)


class OpenAIProvider(LLMProviderBase):
    """Provider implementation for OpenAI LLMs."""

    // ... existing code ...