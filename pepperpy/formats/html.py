"""HTML format handling functionality.

This module provides functionality for processing and transforming HTML content,
including parsing, formatting, and validation.
"""

from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from pepperpy.core.errors.base import PepperError


class ProcessingError(PepperError):
    """Error raised when processing fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(message, details=details if details is not None else {})


class HTMLProcessor:
    """Process and transform HTML content."""

    def __init__(self, parser: str = "html.parser"):
        """Initialize HTML processor.

        Args:
            parser: HTML parser to use (html.parser, lxml, html5lib)

        """
        self.parser = parser

    def parse(self, content: str) -> BeautifulSoup:
        """Parse HTML content into a BeautifulSoup object.

        Args:
            content: HTML content to parse

        Returns:
            BeautifulSoup object representing the HTML

        Raises:
            ProcessingError: If parsing fails

        """
        try:
            return BeautifulSoup(content, self.parser)
        except Exception as e:
            raise ProcessingError(f"HTML parsing failed: {e!s}") from e

    def extract_text(self, content: str) -> str:
        """Extract text from HTML content.

        Args:
            content: HTML content to extract text from

        Returns:
            Extracted text

        Raises:
            ProcessingError: If extraction fails

        """
        try:
            soup = self.parse(content)
            return soup.get_text(separator=" ", strip=True)
        except Exception as e:
            raise ProcessingError(f"HTML text extraction failed: {e!s}") from e

    def extract_links(self, content: str) -> List[Dict[str, str]]:
        """Extract links from HTML content.

        Args:
            content: HTML content to extract links from

        Returns:
            List of dictionaries containing link information

        Raises:
            ProcessingError: If extraction fails

        """
        try:
            soup = self.parse(content)
            links = []
            for link in soup.find_all("a", href=True):
                links.append(
                    {
                        "text": link.get_text(strip=True),
                        "href": link["href"],
                        "title": link.get("title", ""),
                    },
                )
            return links
        except Exception as e:
            raise ProcessingError(f"HTML link extraction failed: {e!s}") from e

    def extract_metadata(self, content: str) -> Dict[str, str]:
        """Extract metadata from HTML content.

        Args:
            content: HTML content to extract metadata from

        Returns:
            Dictionary containing metadata

        Raises:
            ProcessingError: If extraction fails

        """
        try:
            soup = self.parse(content)
            metadata = {}

            # Extract title
            title = soup.find("title")
            if title:
                metadata["title"] = title.get_text(strip=True)

            # Extract meta tags
            for meta in soup.find_all("meta"):
                name = meta.get("name", meta.get("property", ""))
                if name and meta.get("content"):
                    metadata[name] = meta["content"]

            return metadata
        except Exception as e:
            raise ProcessingError(f"HTML metadata extraction failed: {e!s}") from e

    def format(self, content: str, pretty: bool = True) -> str:
        """Format HTML content.

        Args:
            content: HTML content to format
            pretty: Whether to pretty-print the HTML

        Returns:
            Formatted HTML content

        Raises:
            ProcessingError: If formatting fails

        """
        try:
            soup = self.parse(content)
            return soup.prettify() if pretty else str(soup)
        except Exception as e:
            raise ProcessingError(f"HTML formatting failed: {e!s}") from e

    def validate(self, content: str) -> List[str]:
        """Validate HTML content.

        Args:
            content: HTML content to validate

        Returns:
            List of validation errors

        """
        errors = []

        if not content:
            errors.append("Empty content")
            return errors

        try:
            soup = self.parse(content)

            # Check for basic HTML structure
            if not soup.find("html"):
                errors.append("Missing <html> tag")

            if not soup.find("head"):
                errors.append("Missing <head> tag")

            if not soup.find("body"):
                errors.append("Missing <body> tag")

            # Check for required meta tags
            if not soup.find("meta", {"charset": True}):
                errors.append("Missing charset meta tag")

            # Check for broken links
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.startswith("#") and not soup.find(id=href[1:]):
                    errors.append(f"Broken internal link: {href}")

        except Exception as e:
            errors.append(f"HTML validation failed: {e!s}")

        return errors
