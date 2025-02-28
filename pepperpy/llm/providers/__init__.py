"""
COMPATIBILITY STUB: This module has been moved to pepperpy.providers.llm
This stub exists for backward compatibility and will be removed in a future version.
"""

import importlib
import warnings

warnings.warn(
    "The module pepperpy.llm.providers has been moved to pepperpy.providers.llm. "
    "Please update your imports. This stub will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Import the module from the new location
_module = importlib.import_module("pepperpy.providers.llm")

# Copy all attributes from the imported module to this module's namespace
for _attr in dir(_module):
    if not _attr.startswith("_"):
        globals()[_attr] = getattr(_module, _attr)

# Explicitly import specific providers to ensure they're available
from pepperpy.llm.providers.anthropic import AnthropicConfig as AnthropicConfig
from pepperpy.llm.providers.anthropic import AnthropicProvider as AnthropicProvider
from pepperpy.llm.providers.gemini import GeminiConfig as GeminiConfig
from pepperpy.llm.providers.gemini import GeminiProvider as GeminiProvider
from pepperpy.llm.providers.openai import OpenAIConfig as OpenAIConfig
from pepperpy.llm.providers.openai import OpenAIProvider as OpenAIProvider
from pepperpy.llm.providers.openrouter import OpenRouterConfig as OpenRouterConfig
from pepperpy.llm.providers.openrouter import OpenRouterProvider as OpenRouterProvider
from pepperpy.llm.providers.perplexity import PerplexityConfig as PerplexityConfig
from pepperpy.llm.providers.perplexity import PerplexityProvider as PerplexityProvider
