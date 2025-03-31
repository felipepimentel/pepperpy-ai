"""
Provider implementation for mammoth document processing.
"""

from pepperpy.content_processing.base import ContentProcessor, ProcessingResult


class Provider(ContentProcessor):
    """Provider for processing document using mammoth."""

    def __init__(self, **kwargs):
        """Initialize the mammoth document processor."""
        super().__init__(**kwargs)

    async def process(self, content, content_type=None, **kwargs):
        """Process document content using mammoth."""
        # Implementação básica
        return ProcessingResult(text="")
