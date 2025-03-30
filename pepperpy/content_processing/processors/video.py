"""Video processor implementation."""

from pathlib import Path
from typing import Any, Dict, Union

from pepperpy.content_processing.base import (
    ContentProcessor,
    ContentType,
    ProcessingResult,
)
from pepperpy.content_processing.errors import ContentProcessingError


class VideoProcessor(ContentProcessor):
    """Processor for video content."""

    def __init__(
        self,
        provider_type: str = "ffmpeg",
        **kwargs: Any,
    ) -> None:
        """Initialize video processor.

        Args:
            provider_type: Type of provider to use (ffmpeg)
            **kwargs: Additional configuration options passed to the provider
        """
        super().__init__(provider_type, **kwargs)
        self._content_type = ContentType.VIDEO

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
        """Process video content.

        Args:
            content_path: Path to the video file
            **options: Additional processing options
                - format: str - Target format for conversion
                - resolution: Tuple[int, int] - Target resolution (width, height)
                - bitrate: str - Target bitrate (e.g., '2M')
                - fps: int - Target frames per second
                - codec: str - Video codec to use
                - audio_codec: str - Audio codec to use
                - audio_bitrate: str - Target audio bitrate
                - trim: Tuple[float, float] - Start and end time in seconds
                - extract_frames: bool - Extract frames as images
                - frame_interval: float - Interval between extracted frames
                - extract_audio: bool - Extract audio track
                - generate_thumbnail: bool - Generate video thumbnail
                - thumbnail_time: float - Time for thumbnail extraction
                - extract_metadata: bool - Extract video metadata

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
            raise ContentProcessingError(f"Failed to process video: {e}")

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
