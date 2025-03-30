"""FFmpeg provider for audio processing."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.core.utils import lazy_provider_class
from pepperpy.content_processing.base import ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError

try:
    import ffmpeg
except ImportError:
    ffmpeg = None


@lazy_provider_class("content_processing.audio", "ffmpeg")
class FFmpegProvider:
    """Provider for audio processing using FFmpeg."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize FFmpeg provider.

        Args:
            **kwargs: Additional configuration options
        """
        self._config = kwargs
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            if ffmpeg is None:
                raise ContentProcessingError(
                    "FFmpeg-python is not installed. Install with: pip install ffmpeg-python"
                )
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

    async def process(
        self,
        content_path: Union[str, Path],
        **options: Any,
    ) -> ProcessingResult:
        """Process audio using FFmpeg.

        Args:
            content_path: Path to the audio file
            **options: Additional processing options

        Returns:
            Processing result with extracted content

        Raises:
            ContentProcessingError: If processing fails
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Get file info
            probe = ffmpeg.probe(str(content_path))
            audio_info = next(s for s in probe['streams'] if s['codec_type'] == 'audio')

            # Extract metadata
            metadata = {
                'duration': float(probe['format'].get('duration', 0)),
                'format': probe['format']['format_name'],
                'bit_rate': int(probe['format'].get('bit_rate', 0)),
                'size': int(probe['format'].get('size', 0)),
                'sample_rate': int(audio_info.get('sample_rate', 0)),
                'channels': int(audio_info.get('channels', 0)),
                'codec': audio_info.get('codec_name', ''),
            }

            # Return result
            return ProcessingResult(
                metadata=metadata,
            )

        except Exception as e:
            raise ContentProcessingError(f"Failed to process audio with FFmpeg: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            'supports_metadata': True,
            'supports_transcription': False,
            'supported_formats': [
                '.mp3',
                '.wav',
                '.ogg',
                '.m4a',
                '.flac',
                '.aac',
                '.wma',
            ],
        } 