"""Anthropic provider for PepperPy.

This module provides backward compatibility for the Anthropic provider.
The actual implementation has been moved to pepperpy.llm.providers.rest.
"""

# Import from new location for backward compatibility
from pepperpy.llm.providers.rest import AnthropicProvider

__all__ = ["AnthropicProvider"]
