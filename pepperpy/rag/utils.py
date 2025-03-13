"""Utility functions for RAG processing.

This module provides utility functions for document processing in the RAG system,
including text cleaning, HTML/Markdown formatting removal, text chunking,
and metadata extraction for improved retrieval and generation.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Union, cast

import nltk
from bs4 import BeautifulSoup, Tag

from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


def clean_text(
    text: str,
    remove_extra_whitespace: bool = True,
    normalize_unicode: bool = True,
    lowercase: bool = False,
) -> str:
    """Clean and normalize text for improved processing.

    Performs multiple text cleaning operations to standardize text for
    downstream processing, including unicode normalization, whitespace
    removal, and case normalization.

    Args:
        text: The input text to clean
        remove_extra_whitespace: Whether to collapse multiple whitespace
            characters into a single space
        normalize_unicode: Whether to normalize unicode characters to their
            canonical form
        lowercase: Whether to convert all text to lowercase

    Returns:
        str: The cleaned and normalized text

    Example:
        >>> text = "  Hello  World!  "
        >>> clean_text(text)
        'Hello World!'

        >>> text = "Café"
        >>> clean_text(text, normalize_unicode=True)
        'Cafe'

        >>> clean_text("HELLO", lowercase=True)
        'hello'
    """
    if not text:
        return ""

    # Normalize unicode if requested
    if normalize_unicode:
        text = unicodedata.normalize("NFKD", text)
        text = "".join([c for c in text if not unicodedata.combining(c)])

    # Remove extra whitespace if requested
    if remove_extra_whitespace:
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

    # Convert to lowercase if requested
    if lowercase:
        text = text.lower()

    return text


def remove_html_tags(text: str) -> str:
    """Extract plain text content from HTML-formatted text.

    Uses BeautifulSoup to parse HTML and extract the text content,
    removing all HTML tags, attributes, and preserving only the
    textual content.

    Args:
        text: HTML-formatted text to process

    Returns:
        str: Plain text with all HTML elements removed

    Example:
        >>> html = "<p>Hello <b>World</b>!</p>"
        >>> remove_html_tags(html)
        'Hello World!'

        >>> html = "<div>Line 1<br>Line 2</div>"
        >>> remove_html_tags(html)
        'Line 1 Line 2'
    """
    if not text:
        return ""

    # Use BeautifulSoup to parse and extract text
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(" ", strip=True)


def clean_markdown_formatting(text: str) -> str:
    """Remove Markdown formatting while preserving content.

    Strips Markdown syntax elements like headers, emphasis markers,
    code blocks, and links, while preserving the actual content.
    Useful for converting Markdown documents to plain text for
    embedding or analysis.

    Args:
        text: Markdown-formatted text to process

    Returns:
        str: Plain text with Markdown formatting removed

    Example:
        >>> md = "# Title\n\nThis is **bold** and *italic* text."
        >>> clean_markdown_formatting(md)
        'Title\n\nThis is bold and italic text.'

        >>> md = "```python\nprint('hello')\n```"
        >>> clean_markdown_formatting(md)
        "print('hello')"
    """
    if not text:
        return ""

    # Remove headers
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

    # Remove bold/italic markers
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)

    # Remove inline code
    text = re.sub(r"`(.+?)`", r"\1", text)

    # Remove code blocks
    text = re.sub(r"```.*?\n(.*?)```", r"\1", text, flags=re.DOTALL)

    # Remove links
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

    # Remove images
    text = re.sub(r"!\[.*?\]\(.+?\)", "", text)

    # Remove horizontal rules
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Remove blockquotes
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

    # Clean up extra whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def split_text_by_separator(
    text: str, chunk_size: int, chunk_overlap: int, separator: str = "\n"
) -> List[str]:
    """Split text into chunks using a separator.

    Args:
        text: The text to split
        chunk_size: The maximum size of each chunk
        chunk_overlap: The overlap between chunks
        separator: The separator to use for splitting

    Returns:
        The text split into chunks
    """
    if not text:
        return []

    # If the text is smaller than the chunk size, return it as is
    if len(text) <= chunk_size:
        return [text]

    # Split the text by the separator
    splits = text.split(separator)
    chunks = []
    current_chunk = []
    current_length = 0

    for split in splits:
        split_length = len(split) + len(separator)

        # If adding this split would exceed the chunk size,
        # and we already have content in the current chunk,
        # add the current chunk to the list and start a new one
        if current_length + split_length > chunk_size and current_chunk:
            chunks.append(separator.join(current_chunk))

            # Start a new chunk with overlap
            overlap_start = max(0, len(current_chunk) - chunk_overlap)
            current_chunk = current_chunk[overlap_start:]
            current_length = sum(len(s) + len(separator) for s in current_chunk)

        # Add the current split to the chunk
        current_chunk.append(split)
        current_length += split_length

    # Add the last chunk if there's content
    if current_chunk:
        chunks.append(separator.join(current_chunk))

    return chunks


def split_text_by_char(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Split text into chunks based on characters.

    Args:
        text: The text to split
        chunk_size: The maximum size of each chunk
        chunk_overlap: The overlap between chunks

    Returns:
        The text split into chunks
    """
    if not text:
        return []

    # If the text is smaller than the chunk size, return it as is
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        # Define the end of the current chunk
        end = min(start + chunk_size, len(text))

        # Add the chunk to the list
        chunks.append(text[start:end])

        # Move the start to the next chunk, considering overlap
        start = end - chunk_overlap

        # Check if we've reached the end of the text
        if start >= len(text) - chunk_overlap:
            break

    return chunks


def extract_html_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract metadata from HTML.

    Args:
        soup: The BeautifulSoup object

    Returns:
        A dictionary of metadata
    """
    metadata = {}

    # Extract title
    title_tag = soup.find("title")
    if title_tag and isinstance(title_tag, Tag) and title_tag.string:
        metadata["title"] = str(title_tag.string).strip()

    # Extract meta tags
    for meta in soup.find_all("meta"):
        if not isinstance(meta, Tag):
            continue
            
        name = meta.get("name", "")
        if name:
            name = str(name).lower()
            
        content = meta.get("content", "")
        
        if name and content:
            metadata[name] = str(content)

    # Extract Open Graph metadata
    for meta in soup.find_all("meta", property=re.compile(r"^og:")):
        if not isinstance(meta, Tag):
            continue
            
        property_name = meta.get("property", "")
        if property_name and isinstance(property_name, str):
            property_name = property_name[3:]  # Remove 'og:' prefix
            
        content = meta.get("content", "")
        
        if property_name and content:
            metadata[f"og_{property_name}"] = str(content)

    return metadata


def calculate_text_statistics(text: str) -> Dict[str, Any]:
    """Calculate statistics for text.

    Args:
        text: The text to analyze

    Returns:
        A dictionary of statistics
    """
    if not text:
        return {
            "char_count": 0,
            "word_count": 0,
            "line_count": 0,
            "sentence_count": 0,
            "avg_word_length": 0,
            "avg_sentence_length": 0,
        }

    # Basic statistics
    char_count = len(text)
    word_count = len(text.split())
    line_count = text.count("\n") + 1

    # Advanced statistics
    try:
        sentences = nltk.sent_tokenize(text)
        sentence_count = len(sentences)

        words = nltk.word_tokenize(text)
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0

        avg_sentence_length = (
            sum(len(nltk.word_tokenize(sentence)) for sentence in sentences)
            / len(sentences)
            if sentences
            else 0
        )

        return {
            "char_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
            "sentence_count": sentence_count,
            "avg_word_length": round(avg_word_length, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
        }
    except Exception as e:
        logger.warning(f"Error calculating advanced text statistics: {e}")
        return {
            "char_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
        }
