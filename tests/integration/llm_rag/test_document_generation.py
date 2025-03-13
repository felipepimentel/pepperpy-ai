"""Integration tests for document processing and LLM response generation."""

import pytest

from pepperpy.llm.utils import (
    Message,
    Prompt,
    calculate_token_usage,
    format_prompt_for_provider,
    truncate_prompt,
)
from pepperpy.rag.utils import (
    clean_markdown_formatting,
    clean_text,
    split_text_by_separator,
)


def test_document_to_prompt_flow():
    """Test the flow from document processing to prompt creation."""
    # Test document text
    document = """
    # Sample Document

    This is a sample document with multiple paragraphs.
    It contains some Markdown formatting that needs to be cleaned.

    ## Section 1

    - First point
    - Second point
    - Third point

    ```python
    def sample_code():
        return "test"
    ```

    > Some quoted text here.
    """

    # Clean and process the document
    cleaned_text = clean_text(document)
    cleaned_markdown = clean_markdown_formatting(cleaned_text)
    chunks = split_text_by_separator(cleaned_markdown, chunk_size=100, chunk_overlap=20)

    # Create messages from chunks
    messages = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            messages.append(
                Message(role="system", content="Process this document chunk.")
            )
        messages.append(Message(role="user", content=chunk))

    # Create prompt
    prompt = Prompt(messages=messages)

    # Format for different providers
    openai_format = format_prompt_for_provider(prompt, "openai")
    assert isinstance(openai_format, list)
    assert len(openai_format) > 1
    assert all(isinstance(m, dict) for m in openai_format)

    anthropic_format = format_prompt_for_provider(prompt, "anthropic")
    assert isinstance(anthropic_format, str)
    assert len(anthropic_format) > 0


def test_document_chunking_and_token_limits():
    """Test document chunking with token limits."""
    # Create a long document
    paragraphs = ["This is paragraph {}".format(i) for i in range(20)]
    document = "\n\n".join(paragraphs)

    # Clean and chunk the document
    cleaned_text = clean_text(document)
    chunks = split_text_by_separator(cleaned_text, chunk_size=100, chunk_overlap=20)

    # Process each chunk while respecting token limits
    for chunk in chunks:
        # Create a prompt with the chunk
        messages = [
            Message(role="system", content="Process this document chunk."),
            Message(role="user", content=chunk),
        ]
        prompt = Prompt(messages=messages)

        # Check token usage and truncate if needed
        truncated = truncate_prompt(
            prompt, max_tokens=50, provider="test", model="test-model"
        )

        # Verify the truncated prompt
        usage = calculate_token_usage(
            convert_messages_to_text(truncated.messages),
            completion_text="",
            provider="test",
            model="test-model",
        )
        assert usage["prompt_tokens"] <= 50


def test_document_processing_error_handling():
    """Test error handling in document processing and LLM integration."""
    # Test with invalid Markdown
    invalid_markdown = "```unclosed code block"
    cleaned_markdown = clean_markdown_formatting(invalid_markdown)
    assert cleaned_markdown  # Should handle unclosed blocks

    # Test with empty chunks
    chunks = split_text_by_separator("", chunk_size=100, chunk_overlap=20)
    assert chunks == []  # Should handle empty input

    # Test prompt creation with empty messages
    with pytest.raises(Exception):
        Prompt(messages=[])  # Should validate message list

    # Test token calculation with invalid provider
    messages = [Message(role="user", content="Test")]
    prompt = Prompt(messages=messages)
    with pytest.raises(Exception):
        format_prompt_for_provider(prompt, "invalid_provider")
