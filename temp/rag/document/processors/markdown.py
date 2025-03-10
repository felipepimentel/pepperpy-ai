"""Markdown document processor.

This module provides functionality for processing Markdown documents.
"""

import re
from typing import Dict, List, Optional, Union

from pepperpy.rag.document.core import Document, DocumentChunk
from pepperpy.rag.document.processors.text import TextProcessor
from pepperpy.rag.errors import DocumentProcessError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class MarkdownProcessor:
    """Processor for Markdown documents.

    This processor processes Markdown documents by converting to text and splitting into chunks.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n",
        metadata: Optional[Dict[str, str]] = None,
        strip_html: bool = True,
        keep_links: bool = True,
        keep_images: bool = False,
    ):
        """Initialize a Markdown processor.

        Args:
            chunk_size: The maximum size of each chunk in characters
            chunk_overlap: The number of characters to overlap between chunks
            separator: The separator to use when splitting text
            metadata: Additional metadata to add to the chunks
            strip_html: Whether to strip HTML tags from the Markdown
            keep_links: Whether to keep links in the converted text
            keep_images: Whether to keep image references in the converted text
        """
        self.text_processor = TextProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator=separator,
            metadata=metadata,
        )
        self.strip_html = strip_html
        self.keep_links = keep_links
        self.keep_images = keep_images

    async def process(self, document: Document) -> List[DocumentChunk]:
        """Process a document.

        Args:
            document: The document to process

        Returns:
            The processed document chunks

        Raises:
            DocumentProcessError: If there is an error processing the document
        """
        try:
            # Get the document content
            markdown_content = document.content

            # Convert Markdown to text
            text = self._convert_markdown_to_text(markdown_content)

            # Create a new document with the converted text
            text_document = Document(
                content=text,
                metadata=document.metadata,
                id=document.id,
            )

            # Process the text document
            return await self.text_processor.process(text_document)
        except Exception as e:
            raise DocumentProcessError(f"Error processing Markdown document: {e}")

    async def process_batch(self, documents: List[Document]) -> List[DocumentChunk]:
        """Process a batch of documents.

        Args:
            documents: The documents to process

        Returns:
            The processed document chunks

        Raises:
            DocumentProcessError: If there is an error processing the documents
        """
        chunks = []

        for document in documents:
            try:
                document_chunks = await self.process(document)
                chunks.extend(document_chunks)
            except Exception as e:
                logger.error(f"Error processing document {document.id}: {e}")

        return chunks

    def _convert_markdown_to_text(self, markdown_content: str) -> str:
        """Convert Markdown to text.

        Args:
            markdown_content: The Markdown content to convert

        Returns:
            The converted text
        """
        try:
            # Import markdown here to avoid dependency if not used
            import markdown
            from bs4 import BeautifulSoup

            # Convert Markdown to HTML
            html = markdown.markdown(markdown_content)

            # Parse the HTML
            soup = BeautifulSoup(html, "html.parser")

            # Process links
            if not self.keep_links:
                for link in soup.find_all("a"):
                    link.replace_with(link.text)

            # Process images
            if not self.keep_images:
                for img in soup.find_all("img"):
                    img.decompose()

            # Strip HTML if requested
            if self.strip_html:
                text = soup.get_text(separator="\n", strip=True)
            else:
                text = str(soup)

            return text
        except Exception as e:
            logger.error(f"Error converting Markdown to text: {e}")
            return markdown_content

    def _process_headings(self, text: str) -> str:
        """Process Markdown headings.

        Args:
            text: The text to process

        Returns:
            The processed text
        """
        # Replace heading markers with text and newlines
        text = re.sub(r"^# (.+)$", r"\1\n", text, flags=re.MULTILINE)
        text = re.sub(r"^## (.+)$", r"\1\n", text, flags=re.MULTILINE)
        text = re.sub(r"^### (.+)$", r"\1\n", text, flags=re.MULTILINE)
        text = re.sub(r"^#### (.+)$", r"\1\n", text, flags=re.MULTILINE)
        text = re.sub(r"^##### (.+)$", r"\1\n", text, flags=re.MULTILINE)
        text = re.sub(r"^###### (.+)$", r"\1\n", text, flags=re.MULTILINE)

        return text

    def _process_lists(self, text: str) -> str:
        """Process Markdown lists.

        Args:
            text: The text to process

        Returns:
            The processed text
        """
        # Replace list markers with text
        text = re.sub(r"^- (.+)$", r"• \1", text, flags=re.MULTILINE)
        text = re.sub(r"^\* (.+)$", r"• \1", text, flags=re.MULTILINE)
        text = re.sub(r"^\+ (.+)$", r"• \1", text, flags=re.MULTILINE)
        text = re.sub(r"^(\d+)\. (.+)$", r"\1. \2", text, flags=re.MULTILINE)

        return text

    def _process_emphasis(self, text: str) -> str:
        """Process Markdown emphasis.

        Args:
            text: The text to process

        Returns:
            The processed text
        """
        # Replace emphasis markers with text
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"_(.+?)_", r"\1", text)

        return text
