"""Tests for RAG document utility functions."""

import unicodedata

from bs4 import BeautifulSoup

from pepperpy.rag.utils import (
    calculate_text_statistics,
    clean_markdown_formatting,
    clean_text,
    extract_html_metadata,
    remove_html_tags,
    split_text_by_char,
    split_text_by_separator,
)


def test_clean_text():
    """Test text cleaning functionality."""
    # Test whitespace removal
    text = "  Hello   World  \n\n  "
    result = clean_text(text)
    assert result == "Hello World"

    # Test unicode normalization
    text = "café"  # é is a composed character
    result = clean_text(text)
    assert unicodedata.is_normalized("NFKD", result)
    assert result == "cafe"

    # Test lowercase conversion
    text = "Hello World"
    result = clean_text(text, lowercase=True)
    assert result == "hello world"

    # Test with all options disabled
    text = "  Hello   World  \n"
    result = clean_text(
        text,
        remove_extra_whitespace=False,
        normalize_unicode=False,
        lowercase=False,
    )
    assert result == text

    # Test empty input
    assert clean_text("") == ""


def test_remove_html_tags():
    """Test HTML tag removal."""
    # Test basic HTML
    html = "<p>Hello <b>World</b></p>"
    assert remove_html_tags(html) == "Hello World"

    # Test nested tags
    html = "<div><p>Hello <b>World</b></p><p>Test</p></div>"
    assert remove_html_tags(html) == "Hello World Test"

    # Test with attributes
    html = '<p class="test">Hello</p>'
    assert remove_html_tags(html) == "Hello"

    # Test with special characters
    html = "<p>Hello &amp; World</p>"
    assert remove_html_tags(html) == "Hello & World"

    # Test empty input
    assert remove_html_tags("") == ""


def test_clean_markdown_formatting():
    """Test Markdown formatting removal."""
    # Test headers
    text = "# Header 1\n## Header 2"
    assert clean_markdown_formatting(text) == "Header 1\nHeader 2"

    # Test emphasis
    text = "**bold** and *italic* text"
    assert clean_markdown_formatting(text) == "bold and italic text"

    # Test code blocks
    text = "```python\ndef test():\n    pass\n```"
    assert clean_markdown_formatting(text) == "def test():\n    pass"

    # Test inline code
    text = "Use the `print()` function"
    assert clean_markdown_formatting(text) == "Use the print() function"

    # Test links
    text = "[Link text](https://example.com)"
    assert clean_markdown_formatting(text) == "Link text"

    # Test images
    text = "![Alt text](image.png)"
    assert clean_markdown_formatting(text) == ""

    # Test blockquotes
    text = "> Quoted text\n> More text"
    assert clean_markdown_formatting(text) == "Quoted text\nMore text"

    # Test horizontal rules
    text = "Above\n---\nBelow"
    assert clean_markdown_formatting(text) == "Above\nBelow"

    # Test empty input
    assert clean_markdown_formatting("") == ""


def test_split_text_by_separator():
    """Test text splitting by separator."""
    # Test basic splitting
    text = "First chunk\nSecond chunk\nThird chunk"
    chunks = split_text_by_separator(text, chunk_size=15, chunk_overlap=0)
    assert len(chunks) == 3
    assert chunks[0] == "First chunk"
    assert chunks[1] == "Second chunk"
    assert chunks[2] == "Third chunk"

    # Test with overlap
    text = "One\nTwo\nThree\nFour"
    chunks = split_text_by_separator(text, chunk_size=8, chunk_overlap=1)
    assert len(chunks) == 3
    assert "Two" in chunks[0] and "Two" in chunks[1]  # Overlap
    assert "Three" in chunks[1] and "Three" in chunks[2]  # Overlap

    # Test with custom separator
    text = "First|Second|Third"
    chunks = split_text_by_separator(
        text, chunk_size=10, chunk_overlap=0, separator="|"
    )
    assert len(chunks) == 3
    assert chunks[0] == "First"
    assert chunks[1] == "Second"
    assert chunks[2] == "Third"

    # Test text smaller than chunk size
    text = "Small text"
    chunks = split_text_by_separator(text, chunk_size=100, chunk_overlap=0)
    assert len(chunks) == 1
    assert chunks[0] == text

    # Test empty input
    assert split_text_by_separator("", chunk_size=10, chunk_overlap=0) == []


def test_split_text_by_char():
    """Test text splitting by character."""
    # Test basic splitting
    text = "Hello World"
    chunks = split_text_by_char(text, chunk_size=5, chunk_overlap=0)
    assert len(chunks) == 3
    assert chunks[0] == "Hello"
    assert chunks[1] == " Worl"
    assert chunks[2] == "d"

    # Test with overlap
    text = "Hello World"
    chunks = split_text_by_char(text, chunk_size=6, chunk_overlap=2)
    assert len(chunks) == 3
    assert chunks[0] == "Hello "
    assert chunks[1] == "o Worl"
    assert chunks[2] == "rld"

    # Test text smaller than chunk size
    text = "Small"
    chunks = split_text_by_char(text, chunk_size=10, chunk_overlap=0)
    assert len(chunks) == 1
    assert chunks[0] == text

    # Test empty input
    assert split_text_by_char("", chunk_size=10, chunk_overlap=0) == []


def test_extract_html_metadata():
    """Test HTML metadata extraction."""
    # Test basic metadata
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
            <meta name="keywords" content="test, metadata">
        </head>
        <body>Content</body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    metadata = extract_html_metadata(soup)
    assert metadata["title"] == "Test Page"
    assert metadata["description"] == "Test description"
    assert metadata["keywords"] == "test, metadata"

    # Test Open Graph metadata
    html = """
    <html>
        <head>
            <meta property="og:title" content="OG Title">
            <meta property="og:description" content="OG Description">
            <meta property="og:image" content="image.jpg">
        </head>
        <body>Content</body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    metadata = extract_html_metadata(soup)
    assert metadata["og_title"] == "OG Title"
    assert metadata["og_description"] == "OG Description"
    assert metadata["og_image"] == "image.jpg"

    # Test empty page
    html = "<html><head></head><body></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    metadata = extract_html_metadata(soup)
    assert isinstance(metadata, dict)
    assert len(metadata) == 0


def test_calculate_text_statistics():
    """Test text statistics calculation."""
    # Test basic text
    text = "This is a test sentence. Another sentence here!"
    stats = calculate_text_statistics(text)
    assert isinstance(stats, dict)
    assert stats["char_count"] > 0
    assert stats["word_count"] > 0
    assert stats["sentence_count"] == 2
    assert stats["avg_word_length"] > 0
    assert stats["avg_sentence_length"] > 0

    # Test empty text
    stats = calculate_text_statistics("")
    assert stats["char_count"] == 0
    assert stats["word_count"] == 0
    assert stats["sentence_count"] == 0
    assert stats["avg_word_length"] == 0
    assert stats["avg_sentence_length"] == 0

    # Test text with special characters
    text = "Hello! This is a test... With some numbers: 123."
    stats = calculate_text_statistics(text)
    assert stats["char_count"] > 0
    assert stats["word_count"] > 0
    assert stats["sentence_count"] > 0

    # Test text with multiple paragraphs
    text = """
    First paragraph with multiple sentences. Another sentence here.
    
    Second paragraph. With more text.
    """
    stats = calculate_text_statistics(text)
    assert stats["char_count"] > 0
    assert stats["word_count"] > 0
    assert stats["sentence_count"] == 4
    assert stats["paragraph_count"] == 2
