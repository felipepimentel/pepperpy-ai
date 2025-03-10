"""HTML document processor.

This module provides functionality for processing HTML documents.
"""

from typing import Dict, List, Optional

from pepperpy.rag.document.core import Document, DocumentChunk
from pepperpy.rag.document.processors.text import TextProcessor
from pepperpy.rag.errors import DocumentProcessError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class HTMLProcessor:
    """Processor for HTML documents.

    This processor processes HTML documents by extracting text and splitting into chunks.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n",
        metadata: Optional[Dict[str, str]] = None,
        include_comments: bool = False,
        include_scripts: bool = False,
        include_styles: bool = False,
    ):
        """Initialize an HTML processor.

        Args:
            chunk_size: The maximum size of each chunk in characters
            chunk_overlap: The number of characters to overlap between chunks
            separator: The separator to use when splitting text
            metadata: Additional metadata to add to the chunks
            include_comments: Whether to include HTML comments in the extracted text
            include_scripts: Whether to include script tags in the extracted text
            include_styles: Whether to include style tags in the extracted text
        """
        self.text_processor = TextProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator=separator,
            metadata=metadata,
        )
        self.include_comments = include_comments
        self.include_scripts = include_scripts
        self.include_styles = include_styles

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
            html_content = document.content

            # Extract text from HTML
            text = self._extract_text_from_html(html_content)

            # Create a new document with the extracted text
            text_document = Document(
                content=text,
                metadata=document.metadata,
                id=document.id,
            )

            # Process the text document
            return await self.text_processor.process(text_document)
        except Exception as e:
            raise DocumentProcessError(f"Error processing HTML document: {e}")

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

    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract text from HTML content.

        Args:
            html_content: The HTML content to extract text from

        Returns:
            The extracted text
        """
        try:
            # Import BeautifulSoup here to avoid dependency if not used
            from bs4 import BeautifulSoup

            # Parse the HTML
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script tags if not included
            if not self.include_scripts:
                for script in soup.find_all("script"):
                    script.decompose()

            # Remove style tags if not included
            if not self.include_styles:
                for style in soup.find_all("style"):
                    style.decompose()

            # Remove comments if not included
            if not self.include_comments:
                for comment in soup.find_all(
                    string=lambda text: isinstance(text, str)
                    and text.strip().startswith("<!--")
                ):
                    comment.extract()

            # Get the text
            text = soup.get_text(separator="\n", strip=True)

            return text
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return html_content
