"""Base classes and interfaces for Pepperpy providers.

This module defines the core abstractions for providers in the Pepperpy framework.
Providers are responsible for handling specific capabilities like text generation,
code completion, etc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Message:
    """Represents a message in a conversation."""

    role: str
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class Response:
    """Represents a response from a provider."""

    content: str
    role: str = "assistant"
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, int]] = None


@dataclass
class ProviderConfig:
    """Configuration for a provider."""

    name: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class Provider(ABC):
    """Base interface for all providers."""

    @abstractmethod
    def initialize(self, config: ProviderConfig) -> None:
        """Initialize the provider with given configuration."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up any resources used by the provider."""
        pass


class BaseProvider(Provider):
    """Base implementation of the Provider interface."""

    def __init__(self):
        self.config: Optional[ProviderConfig] = None

    def initialize(self, config: ProviderConfig) -> None:
        """Initialize the provider with given configuration."""
        self.config = config

    def cleanup(self) -> None:
        """Clean up any resources used by the provider."""
        self.config = None
