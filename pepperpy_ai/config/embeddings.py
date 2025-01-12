"""Embeddings configuration module."""

from typing import Any

from .capability import CapabilityConfig


class EmbeddingsConfig(CapabilityConfig):
    """Configuration for embeddings.

    This class provides configuration options for embeddings, including model
    settings, normalization options, and other parameters that control the
    embedding generation process.
    """

    def __init__(
        self,
        name: str,
        version: str,
        model: str,
        enabled: bool = True,
        normalize: bool = True,
        batch_size: int = 32,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        api_key: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
        organization_id: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> None:
        """Initialize embeddings configuration.

        Args:
            name: Configuration name.
            version: Configuration version.
            model: Model name or path.
            enabled: Whether embeddings are enabled.
            normalize: Whether to normalize embeddings.
            batch_size: Batch size for embedding generation.
            max_retries: Maximum number of retries.
            retry_delay: Delay between retries in seconds.
            timeout: Operation timeout in seconds.
            api_key: API key for authentication.
            api_base: Base URL for API requests.
            api_version: API version to use.
            organization_id: Organization ID for API requests.
            settings: Additional capability settings.
        """
        super().__init__(
            name=name,
            version=version,
            model=model,
            enabled=enabled,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            batch_size=batch_size,
            api_key=api_key,
            api_base=api_base,
            api_version=api_version,
            organization_id=organization_id,
            settings=settings,
        )
        self.normalize = normalize
