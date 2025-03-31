"""
Provider implementation for opencv image processing.
"""

from pepperpy.content_processing.base import ContentProcessor, ProcessingResult


class Provider(ContentProcessor):
    """Provider for processing image using opencv."""

    def __init__(self, **kwargs):
        """Initialize the opencv image processor."""
        super().__init__(**kwargs)

    async def process(self, content, content_type=None, **kwargs):
        """Process image content using opencv."""
        # Implementação básica
        return ProcessingResult(text="")
