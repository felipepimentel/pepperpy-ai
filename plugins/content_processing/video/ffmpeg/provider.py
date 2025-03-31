"""
Provider implementation for ffmpeg video processing.
"""

from pepperpy.content_processing.base import ContentProcessor, ProcessingResult


class Provider(ContentProcessor):
    """Provider for processing video using ffmpeg."""

    def __init__(self, **kwargs):
        """Initialize the ffmpeg video processor."""
        super().__init__(**kwargs)

    async def process(self, content, content_type=None, **kwargs):
        """Process video content using ffmpeg."""
        # Implementação básica
        return ProcessingResult(text="")
