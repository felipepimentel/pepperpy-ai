"""HTML document loader implementation.

This module provides functionality for loading HTML documents.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup
from bs4.element import Comment, NavigableString, Tag

from pepperpy.errors import DocumentLoadError
from pepperpy.rag.document.loaders.base import BaseDocumentLoader
from pepperpy.rag.storage.types import Document


class HTMLLoader(BaseDocumentLoader):
    """HTML document loader.

    This loader handles HTML documents, with support for cleaning,
    metadata extraction, and optional inclusion of comments and scripts.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        clean_html: bool = True,
        extract_metadata: bool = True,
        include_comments: bool = False,
        include_scripts: bool = False,
        include_styles: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the HTML loader.

        Args:
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Number of characters to overlap between chunks.
            clean_html: Whether to clean and normalize HTML content.
            extract_metadata: Whether to extract metadata from meta tags.
            include_comments: Whether to include HTML comments.
            include_scripts: Whether to include script content.
            include_styles: Whether to include style content.
            metadata: Optional metadata to associate with loaded documents.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(metadata=metadata, **kwargs)
        self.chunk_size = max(1, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, chunk_size - 1))
        self.clean_html = clean_html
        self.extract_metadata = extract_metadata
        self.include_comments = include_comments
        self.include_scripts = include_scripts
        self.include_styles = include_styles

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks.

        Args:
            text: Text to split into chunks.

        Returns:
            List of text chunks.
        """
        # Handle empty or short text
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []

        chunks = []
        start = 0

        while start < len(text):
            # Get chunk of specified size
            end = start + self.chunk_size

            # If this is not the last chunk, try to break at paragraph/heading
            if end < len(text):
                # Try to break at paragraph
                paragraph_break = text.rfind("\n\n", start, end)
                if paragraph_break != -1 and paragraph_break > start:
                    end = paragraph_break

                # Try to break at heading
                elif (
                    heading := text.rfind("\n#", start, end)
                ) != -1 and heading > start:
                    end = heading

                # Try to break at newline
                elif (
                    newline := text.rfind("\n", start, end)
                ) != -1 and newline > start:
                    end = newline

                # Try to break at sentence
                elif (period := text.rfind(". ", start, end)) != -1 and period > start:
                    end = period + 1

                # Try to break at space
                elif (space := text.rfind(" ", start, end)) != -1 and space > start:
                    end = space

            # Add chunk
            chunks.append(text[start:end].strip())

            # Move start position, accounting for overlap
            start = end - self.chunk_overlap

        return chunks

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML document.

        Args:
            soup: BeautifulSoup object.

        Returns:
            Dictionary of metadata.
        """
        metadata = {}

        # Get title
        if title := soup.title:
            metadata["title"] = title.string

        # Get meta tags
        for meta in soup.find_all("meta"):
            # Cast to Tag to access get() method
            meta_tag = cast(Tag, meta)
            name = meta_tag.get("name") or meta_tag.get("property")
            content = meta_tag.get("content")

            if name and content:
                metadata[name] = content

        return metadata

    def _clean_content(self, soup: BeautifulSoup) -> str:
        """Clean and extract content from HTML document.

        Args:
            soup: BeautifulSoup object.

        Returns:
            Cleaned text content.
        """
        # Remove unwanted elements
        for element in soup(["script", "style", "head"]):
            element_tag = cast(Tag, element)
            if (
                (element_tag.name == "script" and not self.include_scripts)
                or (element_tag.name == "style" and not self.include_styles)
                or element_tag.name == "head"
            ):
                element.decompose()

        # Remove comments if not wanted
        if not self.include_comments:
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

        # Process remaining content
        chunks = []
        for element in soup.descendants:
            if isinstance(element, (NavigableString, Comment)):
                # Skip empty strings and unwanted comments
                if not str(element).strip():
                    continue
                if isinstance(element, Comment) and not self.include_comments:
                    continue
                chunks.append(str(element))
            elif isinstance(element, Tag):
                # Add newlines around block elements
                if element.name in {
                    "p",
                    "div",
                    "section",
                    "article",
                    "header",
                    "footer",
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "h6",
                    "li",
                    "br",
                }:
                    chunks.append("\n")

        return " ".join(chunks).strip()

    async def _fetch_url(self, url: str) -> str:
        """Fetch HTML content from a URL.

        Args:
            url: URL to fetch.

        Returns:
            HTML content.

        Raises:
            DocumentLoadError: If fetching fails.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()

        except Exception as e:
            raise DocumentLoadError(f"Error fetching URL: {str(e)}") from e

    async def _load_from_file(
        self,
        file_path: Union[str, Path],
        **kwargs: Any,
    ) -> List[Document]:
        """Load HTML from a file.

        Args:
            file_path: Path to the HTML file.
            **kwargs: Additional arguments.

        Returns:
            List containing the loaded document.

        Raises:
            DocumentLoadError: If file reading fails.
        """
        try:
            # Read file asynchronously
            path = Path(file_path)
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                lambda: path.read_text(encoding="utf-8"),
            )

            # Create document from content
            return await self._load_from_string(content, file_path=path, **kwargs)

        except Exception as e:
            raise DocumentLoadError(f"Error reading HTML file: {str(e)}") from e

    async def _load_from_string(
        self,
        content: str,
        **kwargs: Any,
    ) -> List[Document]:
        """Load HTML from a string.

        Args:
            content: HTML content or URL.
            **kwargs: Additional arguments.

        Returns:
            List containing the loaded document.

        Raises:
            DocumentLoadError: If HTML processing fails.
        """
        try:
            # Check if content is a URL
            parsed_url = urlparse(content)
            if parsed_url.scheme and parsed_url.netloc:
                # Fetch content from URL
                html_content = await self._fetch_url(content)
                source = content
            else:
                # Use content as is
                html_content = content
                source = kwargs.get("file_path")
                source = str(source) if source else None

            # Parse HTML
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract metadata if requested
            doc_metadata = {}
            if self.extract_metadata:
                doc_metadata.update(self._extract_metadata(soup))

            # Add source and content type
            if source:
                doc_metadata.update({
                    "source": source,
                    "content_type": "text/html",
                })

            # Clean and extract content
            text = self._clean_content(soup)
            if not text:
                return []

            # Split into chunks
            chunk_texts = self._chunk_text(text)

            # Create document chunks
            chunks = []
            for i, chunk_text in enumerate(chunk_texts):
                chunk = Document.Chunk(
                    content=chunk_text,
                    metadata={
                        "chunk_index": i,
                        "total_chunks": len(chunk_texts),
                    },
                )
                chunks.append(chunk)

            # Create document
            if not chunks:
                return []

            doc = Document(
                chunks=chunks,
                metadata={
                    **doc_metadata,
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "clean_html": self.clean_html,
                    "extract_metadata": self.extract_metadata,
                    "include_comments": self.include_comments,
                    "include_scripts": self.include_scripts,
                    "include_styles": self.include_styles,
                },
            )

            return [doc]

        except Exception as e:
            raise DocumentLoadError(f"Error processing HTML content: {str(e)}") from e
