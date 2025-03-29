"""Main PepperPy module.

This module provides the main PepperPy class with a fluent API for
interacting with the framework's components.
"""

import os
from typing import Any, Dict, Optional

from pepperpy.core.config import Config
from pepperpy.llm import LLMProvider
from pepperpy.llm import create_provider as create_llm_provider


class PepperPy:
    """Main PepperPy class with fluent API."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize PepperPy.

        Args:
            config: Optional configuration dictionary
        """
        self.config = Config(config)
        self._llm: Optional[LLMProvider] = None

    def with_llm(
        self, provider_type: Optional[str] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure LLM provider.

        Args:
            provider_type: Type of LLM provider (defaults to PEPPERPY_LLM__PROVIDER)
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        provider_type = provider_type or os.getenv("PEPPERPY_LLM__PROVIDER", "openai")
        provider_config = self.config.get("llm.config", {})
        provider_config.update(kwargs)

        self._llm = create_llm_provider(provider_type=provider_type, **provider_config)
        return self

    @property
    def llm(self) -> LLMProvider:
        """Get LLM provider."""
        if not self._llm:
            raise ValueError("LLM provider not configured. Call with_llm() first.")
        return self._llm

    async def __aenter__(self) -> "PepperPy":
        """Enter async context."""
        if self._llm:
            await self._llm.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        if self._llm:
            await self._llm.cleanup()
