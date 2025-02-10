"""Model providers for the Pepperpy framework.

This module provides integrations with various AI model providers, including OpenAI
and Anthropic, with a consistent interface for model interactions.
"""

from pepperpy.providers.base import BaseProvider, ProviderConfig
from pepperpy.providers.services.openai import OpenAIConfig, OpenAIProvider

__all__ = [
    "BaseProvider",
    "OpenAIConfig",
    "OpenAIProvider",
    "ProviderConfig",
]

# Version information
__version__ = "1.0.0"
__author__ = "Pepperpy Team"
