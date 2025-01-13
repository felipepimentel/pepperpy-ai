"""LLM configuration."""

from typing import NotRequired

from ..providers.config import ProviderConfig


class LLMConfig(ProviderConfig):
    """LLM configuration."""

    stop_sequences: NotRequired[list[str]]
