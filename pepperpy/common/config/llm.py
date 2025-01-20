"""Configuration for language models."""

from dataclasses import dataclass
from typing import Dict, Literal, Optional

from .base import BaseConfig, ConfigError
from .validation import ValidationMixin


@dataclass
class OpenAIConfig(ValidationMixin):
    """Configuration for OpenAI models."""
    
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    def validate(self) -> None:
        """Validate OpenAI configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_string("model", self.model, min_length=1)
        self.validate_range("temperature", self.temperature, 0, 2)
        self.validate_positive("max_tokens", self.max_tokens)
        self.validate_range("top_p", self.top_p, 0, 1)
        self.validate_range("frequency_penalty", self.frequency_penalty, -2, 2)
        self.validate_range("presence_penalty", self.presence_penalty, -2, 2)


@dataclass
class AnthropicConfig(ValidationMixin):
    """Configuration for Anthropic models."""
    
    model: str = "claude-2"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_k: int = 40
    top_p: float = 1.0
    
    def validate(self) -> None:
        """Validate Anthropic configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_string("model", self.model, min_length=1)
        self.validate_range("temperature", self.temperature, 0, 1)
        self.validate_positive("max_tokens", self.max_tokens)
        self.validate_positive("top_k", self.top_k)
        self.validate_range("top_p", self.top_p, 0, 1)


@dataclass
class LLMConfig(BaseConfig, ValidationMixin):
    """Configuration for language models."""
    
    default_provider: Literal["openai", "anthropic"] = "openai"
    openai: OpenAIConfig = OpenAIConfig()
    anthropic: AnthropicConfig = AnthropicConfig()
    
    def validate(self) -> None:
        """Validate LLM configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_string(
            "default_provider",
            self.default_provider,
            choices=("openai", "anthropic")
        )
        self.openai.validate()
        self.anthropic.validate() 