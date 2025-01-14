"""RAG configuration module."""

from typing import Any

from .capability import CapabilityConfig


class RAGConfig(CapabilityConfig):
    """Configuration for RAG (Retrieval-Augmented Generation).

    This class provides configuration options for RAG, including model
    settings, chunking parameters, and other options that control the
    retrieval and generation process.
    """

    def __init__(
        self,
        name: str,
        version: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        model: str | None = None,
        enabled: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        batch_size: int = 32,
        api_key: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
        organization_id: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> None:
        """Initialize RAG configuration.

        Args:
            name: Configuration name.
            version: Configuration version.
            chunk_size: Size of text chunks.
            chunk_overlap: Overlap between chunks.
            model: Model to use.
            enabled: Whether capability is enabled.
            max_retries: Maximum number of retries.
            retry_delay: Delay between retries in seconds.
            timeout: Operation timeout in seconds.
            batch_size: Batch size for operations.
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
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
