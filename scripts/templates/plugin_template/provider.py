"""Template provider for DOMAIN tasks.

This module provides a template for implementing new providers in PepperPy,
following all best practices and guidelines.
"""

from typing import Any, Optional

# Import domain-specific types
from pepperpy.DOMAIN import DomainProvider
from pepperpy.plugin import ProviderPlugin


class TemplateProvider(DomainProvider, ProviderPlugin):
    """Template provider for DOMAIN tasks."""

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    # Para valores que podem vir de variáveis de ambiente (nunca devem ter padrão no código)
    api_key: str

    # Para valores fixos ou com padrões sensatos, definir valores padrão
    base_url: str = "https://api.example.com/v1"  # Valor fixo como fallback
    model: str = "default-model"  # Fallback padrão
    temperature: float = 0.7  # Valor padrão sensato
    max_tokens: int = 1024  # Valor padrão sensato
    client: Optional[Any] = None

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the provider."""
        super().__init__(**kwargs)
        self.client = None

        # Garantir que valores fixos estão definidos - usar kwargs, depois os padrões da classe
        if "base_url" in kwargs:
            self.base_url = kwargs["base_url"]
        if "model" in kwargs:
            self.model = kwargs["model"]
        if "temperature" in kwargs:
            self.temperature = kwargs["temperature"]
        if "max_tokens" in kwargs:
            self.max_tokens = kwargs["max_tokens"]

    async def initialize(self) -> None:
        """Initialize provider resources."""
        # Initialize client using auto-bound attributes
        self.client = SomeClient(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    # Implement domain-specific methods
    async def domain_method(self, input_data: Any, **kwargs: Any) -> Any:
        """Implement a domain-specific method."""
        # Use auto-bound attributes with kwargs overrides
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        model = kwargs.get("model", self.model)

        # Initialize if needed
        if not self.client:
            await self.initialize()
            assert self.client is not None

        # Call client API
        response = await self.client.method(
            input=input_data,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Process and return results
        return response

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self.client:
            # Close client connection if needed
            await self.client.aclose()
            self.client = None
