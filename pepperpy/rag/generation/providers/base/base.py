"""Base class for generation providers.

This module provides the base class for all generation providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pepperpy.core.logging import get_logger
from pepperpy.rag.generation.base import Generator
from pepperpy.rag.generation.providers.base.types import (
    GenerationProviderType,
    GenerationRequest,
    GenerationResponse,
)

logger = get_logger(__name__)


class GenerationProvider(Generator, ABC):
    """Base class for all generation providers."""

    def __init__(
        self,
        component_id: str,
        name: str,
        provider_type: GenerationProviderType,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the generation provider.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name for the component
            provider_type: The type of provider
            description: Description of the component's functionality
            config: Configuration for the provider
        """
        super().__init__(component_id, name, description)
        self.provider_type = provider_type
        self.config = config or {}

    @abstractmethod
    async def generate_response(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a response for the given request.

        Args:
            request: The generation request

        Returns:
            The generated response
        """
        pass

    async def initialize(self) -> None:
        """Initialize the provider."""
        logger.debug(f"Initializing generation provider: {self.component_id}")

    async def cleanup(self) -> None:
        """Clean up the provider."""
        logger.debug(f"Cleaning up generation provider: {self.component_id}")
