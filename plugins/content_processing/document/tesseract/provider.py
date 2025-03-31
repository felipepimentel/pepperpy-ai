"""
Provider implementation for tesseract document processing.
"""

from pepperpy.content_processing.base import ContentProcessor, ProcessingResult


class Provider(ContentProcessor):
    """Provider for processing document using tesseract."""

    def __init__(self, **kwargs):
        """Initialize the tesseract document processor."""
        super().__init__(**kwargs)

    async def process(self, content, content_type=None, **kwargs):
        """Process document content using tesseract."""
        # Implementação básica
        return ProcessingResult(text="")
