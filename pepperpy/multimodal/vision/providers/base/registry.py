"""Registry for vision providers."""

from typing import Dict, Type

from pepperpy.multimodal.vision.providers.base.base import VisionProvider


class VisionProviderRegistry:
    """Registry for vision providers."""

    _providers: Dict[str, Type[VisionProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[VisionProvider]) -> None:
        """Register a vision provider.

        Args:
            name: Name of the provider
            provider_cls: Provider class
        """
        cls._providers[name] = provider_cls

    @classmethod
    def get(cls, name: str) -> Type[VisionProvider]:
        """Get a vision provider by name.

        Args:
            name: Name of the provider

        Returns:
            Provider class

        Raises:
            KeyError: If provider is not registered
        """
        if name not in cls._providers:
            raise KeyError(f"Vision provider '{name}' not registered")
        return cls._providers[name]

    @classmethod
    def list(cls) -> Dict[str, Type[VisionProvider]]:
        """List all registered vision providers.

        Returns:
            Dict of provider names to provider classes
        """
        return cls._providers.copy()
