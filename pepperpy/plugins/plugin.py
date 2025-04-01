"""Base plugin interface for PepperPy."""

from typing import Any, Dict, Self


class PepperpyPlugin:
    """Base class for all PepperPy plugins."""

    # Plugin metadata
    plugin_type: str = ""  # Type of plugin (e.g., "llm", "rag", "embeddings")
    provider_type: str = ""  # Type of provider (e.g., "openai", "anthropic", "local")
    version: str = "0.1.0"  # Plugin version

    def __init__(self, **kwargs: Any) -> None:
        """Initialize plugin.

        Args:
            **kwargs: Configuration options
        """
        self._initialized = False
        self._config = kwargs

    async def __aenter__(self) -> Self:
        """Enter async context.

        Returns:
            Self for async context management
        """
        await self.initialize()
        return self

    async def __aexit__(self, *_: Any) -> None:
        """Exit async context."""
        await self.cleanup()

    @property
    def initialized(self) -> bool:
        """Check if plugin is initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate plugin configuration.

        Args:
            config: Configuration to validate

        Raises:
            ValidationError: If configuration is invalid
        """
        pass

    async def initialize(self) -> None:
        """Initialize plugin.

        This method should be overridden by subclasses to perform
        any necessary initialization.

        Raises:
            ValidationError: If initialization fails
        """
        if self.initialized:
            return

        # Validate configuration
        self.validate_config(self._config)
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up plugin resources.

        This method should be overridden by subclasses to perform
        any necessary cleanup.
        """
        self._initialized = False
