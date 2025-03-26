"""LLM workflow component implementation."""

from typing import Any, Dict, List, Optional

from pepperpy.llm.base import LLMProvider
from pepperpy.workflow.components import Component, ComponentError


class LLMComponent(Component):
    """LLM workflow component.

    This component provides LLM capabilities to workflows by wrapping
    an LLMProvider instance.
    """

    def __init__(
        self,
        name: str = "llm",
        provider: Optional[LLMProvider] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize LLM component.

        Args:
            name: Component name
            provider: Optional LLMProvider instance
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(
            name=name,
            type="processor",
            config=config or {},
            metadata=kwargs.get("metadata"),
        )
        self.provider = provider
        self._config.update(kwargs)

    async def initialize(self) -> None:
        """Initialize the component.

        Raises:
            ComponentError: If initialization fails
        """
        if not self.provider:
            provider_name = self._config.get("provider", "openai")
            try:
                # Import the provider dynamically
                module_name = f"pepperpy.llm.providers.{provider_name}"
                try:
                    import importlib

                    provider_module = importlib.import_module(module_name)
                    provider_class = getattr(
                        provider_module, f"{provider_name.title()}Provider"
                    )
                    self.provider = provider_class(
                        name=provider_name, config=self._config
                    )
                except (ImportError, AttributeError) as e:
                    raise ComponentError(f"Provider {provider_name} not found: {e}")
            except Exception as e:
                raise ComponentError(f"Failed to create LLM provider: {e}")

        try:
            await self.provider.initialize()
        except Exception as e:
            raise ComponentError(f"Failed to initialize LLM provider: {e}")

    async def process(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Process messages using the LLM provider.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional provider options

        Returns:
            Model response

        Raises:
            ComponentError: If processing fails
        """
        if not self.provider:
            raise ComponentError("LLM provider not initialized")

        try:
            return await self.provider.chat(messages, **kwargs)
        except Exception as e:
            raise ComponentError(f"LLM processing failed: {e}")

    async def cleanup(self) -> None:
        """Clean up component resources."""
        if self.provider:
            await self.provider.cleanup()
