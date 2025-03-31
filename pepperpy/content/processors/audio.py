"""Audio processor implementation."""

from pathlib import Path
from typing import Any, Dict, Union

from pepperpy.content.base import (
    ContentProcessor,
    ContentType,
    ProcessingResult,
)
from pepperpy.content.errors import ContentProcessingError


class AudioProcessor(ContentProcessor):
    """Processor for audio content."""

    def __init__(
        self,
        provider_type: str = "ffmpeg",
        **kwargs: Any,
    ) -> None:
        """Initialize audio processor.

        Args:
            provider_type: Type of provider to use (ffmpeg)
            **kwargs: Additional configuration options passed to the provider
        """
        super().__init__(provider_type, **kwargs)
        self._content_type = ContentType.AUDIO

    async def initialize(self) -> None:
        """Initialize the processor."""
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        await super().cleanup()

    async def process(
        self,
        content_path: Union[str, Path],
        **options: Any,
    ) -> ProcessingResult:
        """Process audio content.

        Args:
            content_path: Path to the audio file
            **options: Additional processing options
                - format: str - Target format for conversion
                - bitrate: str - Target bitrate (e.g., '192k')
                - sample_rate: int - Target sample rate in Hz
                - channels: int - Number of audio channels
                - normalize: bool - Normalize audio levels
                - trim: Tuple[float, float] - Start and end time in seconds
                - fade: Dict[str, float] - Fade in/out duration in seconds
                - volume: float - Volume adjustment factor
                - speed: float - Playback speed factor
                - extract_metadata: bool - Extract audio metadata

        Returns:
            Processing result with extracted content and metadata

        Raises:
            ContentProcessingError: If processing fails
            UnsupportedContentTypeError: If content type is not supported
        """
        # Validate content type
        if not isinstance(content_path, (str, Path)):
            raise ContentProcessingError("Content path must be a string or Path object")

        content_path = Path(content_path)
        if not content_path.exists():
            raise ContentProcessingError(f"Content path does not exist: {content_path}")

        # Process content
        try:
            result = await self._provider.process(content_path, **options)
            result.metadata["content_type"] = self._content_type.value
            return result

        except Exception as e:
            raise ContentProcessingError(f"Failed to process audio: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get processor capabilities.

        Returns:
            Dictionary of processor capabilities
        """
        capabilities = {
            "content_type": self._content_type.value,
            "provider_type": self._provider_type,
        }
        capabilities.update(self._provider.get_capabilities())
        return capabilities
