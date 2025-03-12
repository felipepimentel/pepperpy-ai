"""LLM module for PepperPy.

This module provides functionality for working with Large Language Models
in the PepperPy framework. It offers a unified interface for generating text
and embeddings using various LLM providers.

Example:
    >>> import pepperpy as pp
    >>> result = await pp.llm.generate("Explain quantum computing in simple terms")
    >>> print(result.data)
    Quantum computing is like regular computing but instead of using bits...
"""

# Import provider module
from pepperpy.llm import providers
from pepperpy.llm.public import (
    embed,
    generate,
    get_provider,
    list_providers,
    register_provider,
)

__all__ = [
    # Public API
    "embed",
    "generate",
    "get_provider",
    "list_providers",
    "register_provider",
    # Modules
    "providers",
]
