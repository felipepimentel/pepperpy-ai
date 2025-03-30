"""FFmpeg provider for video processing."""

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


@lazy_provider_class("content_processing.video", "ffmpeg")
class FFmpegProvider:
    """Provider for video processing using FFmpeg."""

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
        """Process video using FFmpeg.

        Args:
            content_path: Path to the video file
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
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            audio_info = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)

            # Extract metadata
            metadata = {
                'duration': float(probe['format'].get('duration', 0)),
                'format': probe['format']['format_name'],
                'bit_rate': int(probe['format'].get('bit_rate', 0)),
                'size': int(probe['format'].get('size', 0)),
                'video': {
                    'codec': video_info.get('codec_name', ''),
                    'width': int(video_info.get('width', 0)),
                    'height': int(video_info.get('height', 0)),
                    'fps': float(eval(video_info.get('r_frame_rate', '0/1'))),
                    'bit_rate': int(video_info.get('bit_rate', 0)),
                },
            }

            # Add audio info if available
            if audio_info:
                metadata['audio'] = {
                    'codec': audio_info.get('codec_name', ''),
                    'sample_rate': int(audio_info.get('sample_rate', 0)),
                    'channels': int(audio_info.get('channels', 0)),
                    'bit_rate': int(audio_info.get('bit_rate', 0)),
                }

            # Extract thumbnail if requested
            if options.get('extract_thumbnail'):
                try:
                    # Generate thumbnail path
                    thumbnail_path = Path(str(content_path) + '_thumb.jpg')
                    
                    # Extract thumbnail frame
                    stream = ffmpeg.input(str(content_path), ss=1)  # Get frame at 1 second
                    stream = ffmpeg.output(stream, str(thumbnail_path), vframes=1)
                    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)

                    # Add thumbnail path to metadata
                    metadata['thumbnail_path'] = str(thumbnail_path)
                except Exception as e:
                    # Don't fail if thumbnail extraction fails
                    metadata['thumbnail_error'] = str(e)

            # Return result
            return ProcessingResult(
                metadata=metadata,
            )

        except Exception as e:
            raise ContentProcessingError(f"Failed to process video with FFmpeg: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            'supports_metadata': True,
            'supports_thumbnails': True,
            'supports_transcoding': True,
            'supported_formats': [
                '.mp4',
                '.avi',
                '.mov',
                '.mkv',
                '.webm',
                '.flv',
                '.wmv',
                '.m4v',
                '.3gp',
            ],
        } 