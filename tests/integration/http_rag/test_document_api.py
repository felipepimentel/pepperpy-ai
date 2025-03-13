"""Integration tests for HTTP API and RAG document processing."""

import json

import pytest
from bs4 import BeautifulSoup

from pepperpy.http.utils import (
    format_headers,
    get_content_type,
    is_json_content,
)
from pepperpy.rag.utils import (
    clean_markdown_formatting,
    clean_text,
    extract_html_metadata,
    split_text_by_separator,
)


def test_document_upload_processing():
    """Test processing of document uploads through API."""
    # Test request headers
    headers = {
        "Content-Type": "text/markdown",
        "Accept": "application/json",
    }
    formatted_headers = format_headers(headers)
    content_type = get_content_type(formatted_headers)
    assert content_type == "text/markdown"

    # Test document content
    document = """
    # Test Document

    This is a test document with some Markdown formatting.
    It will be processed through the API.

    ## Section 1

    - First point
    - Second point

    ```python
    def test():
        pass
    ```
    """

    # Process document
    cleaned_text = clean_text(document)
    cleaned_markdown = clean_markdown_formatting(cleaned_text)
    chunks = split_text_by_separator(cleaned_markdown, chunk_size=100, chunk_overlap=20)

    # Create API response
    api_response = {
        "document_id": "test-123",
        "chunks": chunks,
        "metadata": {
            "title": "Test Document",
            "section_count": len(chunks),
            "total_length": len(cleaned_text),
        },
    }

    # Verify response format
    response_json = json.dumps(api_response)
    parsed_response = json.loads(response_json)
    assert "document_id" in parsed_response
    assert "chunks" in parsed_response
    assert "metadata" in parsed_response


def test_html_document_processing():
    """Test processing of HTML documents through API."""
    # Test request headers
    headers = {
        "Content-Type": "text/html",
        "Accept": "application/json",
    }
    formatted_headers = format_headers(headers)
    content_type = get_content_type(formatted_headers)
    assert content_type == "text/html"

    # Test HTML document
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
            <meta property="og:title" content="OG Title">
        </head>
        <body>
            <h1>Test Document</h1>
            <p>This is a test paragraph.</p>
            <div class="content">
                <p>More content here.</p>
                <ul>
                    <li>First item</li>
                    <li>Second item</li>
                </ul>
            </div>
        </body>
    </html>
    """

    # Parse and extract metadata
    soup = BeautifulSoup(html, "html.parser")
    metadata = extract_html_metadata(soup)

    # Clean and process content
    text_content = soup.get_text()
    cleaned_text = clean_text(text_content)
    chunks = split_text_by_separator(cleaned_text, chunk_size=100, chunk_overlap=20)

    # Create API response
    api_response = {
        "document_id": "test-456",
        "chunks": chunks,
        "metadata": {
            **metadata,
            "section_count": len(chunks),
            "total_length": len(cleaned_text),
        },
    }

    # Verify response format
    response_json = json.dumps(api_response)
    parsed_response = json.loads(response_json)
    assert "document_id" in parsed_response
    assert "chunks" in parsed_response
    assert "metadata" in parsed_response
    assert "title" in parsed_response["metadata"]


def test_document_api_error_handling():
    """Test error handling in document processing API."""
    # Test invalid content type
    headers = {"content-type": "application/octet-stream"}
    formatted_headers = format_headers(headers)
    with pytest.raises(Exception):
        assert not is_json_content(formatted_headers)

    # Test empty document
    empty_response = {
        "error": "Empty document",
        "code": "EMPTY_DOCUMENT",
    }
    response_json = json.dumps(empty_response)
    parsed_response = json.loads(response_json)
    assert "error" in parsed_response
    assert "code" in parsed_response

    # Test invalid chunk size
    with pytest.raises(Exception):
        split_text_by_separator("test", chunk_size=0, chunk_overlap=0)

    # Test invalid overlap size
    with pytest.raises(Exception):
        split_text_by_separator("test", chunk_size=10, chunk_overlap=20)
