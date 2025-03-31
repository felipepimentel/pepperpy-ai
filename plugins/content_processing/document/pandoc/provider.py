"""
Provider implementation for pandoc document processing.
"""

from pepperpy.content_processing.base import ContentProcessor, ProcessingResult


class Provider(ContentProcessor):
    """Provider for processing document using pandoc."""

    def __init__(self, **kwargs):
        """Initialize the pandoc document processor."""
        super().__init__(**kwargs)

    async def process(self, content, content_type=None, **kwargs):
        """Process document content using pandoc."""
        # Implementação básica
        return ProcessingResult(text="")
