"""Provider registration.

This module handles provider registration for all available providers.
"""

from pepperpy.core.logging import get_logger
from pepperpy.providers.base import ProviderRegistry
from pepperpy.providers.llm.openai import OpenAIProvider

# Configure logging
logger = get_logger(__name__)

# Create global provider registry
registry = ProviderRegistry()

# Register LLM providers
registry.register_provider("openai", OpenAIProvider)

# Export registry
__all__ = ["registry"]
