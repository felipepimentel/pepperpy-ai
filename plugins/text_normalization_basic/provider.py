"""Basic text normalization provider for PepperPy."""

from typing import Any, Optional

from pepperpy.content_processing.processors.text_normalization_base import (
    BaseTextNormalizer,
    TextNormalizerRegistry,
)


class BasicTextNormalizer(BaseTextNormalizer):
    """Basic text normalization provider.

    This provider implements the TextNormalizer interface and extends
    the BaseTextNormalizer with plugin management capabilities.
    """

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
    client: Optional[Any]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the basic text normalizer.

        Args:
            **kwargs: Configuration options
        """
        # Get configuration
        transformations = kwargs.get("transformations")
        custom_patterns = kwargs.get("custom_patterns")
        custom_replacements = kwargs.get("custom_replacements")
        language = kwargs.get("language", "en")

        # Initialize base normalizer
        super().__init__(
            transformations=transformations,
            custom_patterns=custom_patterns,
            custom_replacements=custom_replacements,
            language=language,
            **kwargs,
        )

        # Initialize provider state
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is required by the BaseProvider interface.
        """
        # Nothing to initialize for this simple provider
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is required by the BaseProvider interface.
        """
        # Nothing to clean up for this simple provider
        self.initialized = False


# Register the plugin's normalizer in the registry
TextNormalizerRegistry.register("basic", BasicTextNormalizer)


# Provider factory function (required by plugin system)
def create_provider(**kwargs: Any) -> BasicTextNormalizer:
    """Create a basic text normalizer provider.

    Args:
        **kwargs: Configuration options

    Returns:
        BasicTextNormalizer instance
    """
    return BasicTextNormalizer(**kwargs)
