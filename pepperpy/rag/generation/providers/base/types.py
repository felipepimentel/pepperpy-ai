"""Types for generation providers.

This module provides type definitions for generation providers.
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional


class GenerationProviderType(Enum):
    """Types of generation providers."""

    OPENAI = auto()
    ANTHROPIC = auto()
    LLAMA = auto()
    CUSTOM = auto()


class GenerationRequest:
    """Request for generation."""

    def __init__(
        self,
        prompt: str,
        context: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stop_sequences: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the generation request.

        Args:
            prompt: The prompt to generate from
            context: Optional context to include in the generation
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
            top_p: Top-p sampling parameter
            stop_sequences: Sequences that stop generation
            options: Additional provider-specific options
        """
        self.prompt = prompt
        self.context = context or []
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.stop_sequences = stop_sequences or []
        self.options = options or {}


class GenerationResponse:
    """Response from generation."""

    def __init__(
        self,
        text: str,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the generation response.

        Args:
            text: The generated text
            usage: Token usage information
            metadata: Additional metadata about the generation
        """
        self.text = text
        self.usage = usage or {}
        self.metadata = metadata or {}