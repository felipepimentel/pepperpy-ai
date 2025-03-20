#!/usr/bin/env python
"""Example demonstrating chainable API methods for composition.

This example shows how to use the chainable API methods provided by the
PepperPy framework to compose complex operations in a readable and maintainable way.

Purpose:
    Demonstrate how to use chainable API methods for composition in PepperPy.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install -e .

    2. Run the example:
       python examples/chainable_api_example.py
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict

# Import directly from the module since the chainable module is new
# and may not be exposed in the public API yet
from pepperpy.core.chainable import (
    ChainableMethod,
    chainable,
    create_chainable_operation,
    create_pipeline,
)
from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TextDocument:
    """Simple text document class for demonstration purposes."""

    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# Define chainable text processing functions
@chainable(name="to_upper", description="Convert text to uppercase")
def to_upper(text: str) -> str:
    """Convert text to uppercase.

    Args:
        text: The text to convert

    Returns:
        The uppercase text
    """
    return text.upper()


@chainable(name="to_lower", description="Convert text to lowercase")
def to_lower(text: str) -> str:
    """Convert text to lowercase.

    Args:
        text: The text to convert

    Returns:
        The lowercase text
    """
    return text.lower()


@chainable(name="capitalize", description="Capitalize the first letter of each word")
def capitalize(text: str) -> str:
    """Capitalize the first letter of each word.

    Args:
        text: The text to capitalize

    Returns:
        The capitalized text
    """
    return text.title()


@chainable(name="reverse", description="Reverse the text")
def reverse(text: str) -> str:
    """Reverse the text.

    Args:
        text: The text to reverse

    Returns:
        The reversed text
    """
    return text[::-1]


@chainable(name="add_prefix", description="Add a prefix to the text")
def add_prefix(text: str, prefix: str) -> str:
    """Add a prefix to the text.

    Args:
        text: The text to modify
        prefix: The prefix to add

    Returns:
        The text with the prefix added
    """
    return f"{prefix}{text}"


@chainable(name="add_suffix", description="Add a suffix to the text")
def add_suffix(text: str, suffix: str) -> str:
    """Add a suffix to the text.

    Args:
        text: The text to modify
        suffix: The suffix to add

    Returns:
        The text with the suffix added
    """
    return f"{text}{suffix}"


@chainable(name="replace", description="Replace text in the string")
def replace(text: str, old: str, new: str) -> str:
    """Replace text in the string.

    Args:
        text: The text to modify
        old: The text to replace
        new: The replacement text

    Returns:
        The text with replacements
    """
    return text.replace(old, new)


@chainable(name="trim", description="Remove whitespace from the beginning and end")
def trim(text: str) -> str:
    """Remove whitespace from the beginning and end.

    Args:
        text: The text to trim

    Returns:
        The trimmed text
    """
    return text.strip()


# Define document processing functions
@chainable(name="process_content", description="Process document content")
def process_content(doc: TextDocument, processor: ChainableMethod) -> TextDocument:
    """Process document content.

    Args:
        doc: The document to process
        processor: The processor to apply to the content

    Returns:
        The processed document
    """
    doc.content = processor(doc.content)
    return doc


@chainable(name="add_metadata", description="Add metadata to document")
def add_metadata(doc: TextDocument, key: str, value: Any) -> TextDocument:
    """Add metadata to document.

    Args:
        doc: The document to modify
        key: The metadata key
        value: The metadata value

    Returns:
        The modified document
    """
    doc.metadata[key] = value
    return doc


async def example_basic_chaining():
    """Demonstrate basic method chaining."""
    print("\n=== Basic Method Chaining Example ===")

    # Create a simple chain of text transformations
    text = "hello, world!"
    print(f"Original text: {text}")

    # Chain methods directly
    processor = to_upper().then(add_prefix("Processed: ")).then(add_suffix("!"))
    result = processor(text)
    print(f"Processed text: {result}")

    # Create a more complex chain
    complex_processor = (
        trim()
        .then(capitalize())
        .then(replace("World", "PepperPy"))
        .then(add_prefix("Greeting: "))
        .then(add_suffix(" (processed)"))
    )
    complex_result = complex_processor("  hello, world!  ")
    print(f"Complex processed text: {complex_result}")

    return result


async def example_pipeline():
    """Demonstrate using a pipeline for composition."""
    print("\n=== Pipeline Example ===")

    # Create a pipeline for text processing
    pipeline = (
        create_pipeline("text_pipeline")
        .add_step(trim())
        .add_step(capitalize())
        .add_step(replace("World", "PepperPy"))
        .add_step(add_prefix("Greeting: "))
        .add_step(add_suffix(" (processed)"))
        .with_metadata("purpose", "demonstration")
        .with_metadata("created_by", "example")
    )

    # Execute the pipeline
    text = "  hello, world!  "
    print(f"Original text: {text}")
    result = pipeline.execute(text)
    print(f"Pipeline result: {result}")

    return result


async def example_document_processing():
    """Demonstrate document processing with chainable methods."""
    print("\n=== Document Processing Example ===")

    # Create a document
    doc = TextDocument(
        id="doc1",
        content="hello, world!",
        metadata={"created_at": "2025-03-21"},
    )
    print(f"Original document: {doc}")

    # Process the document
    processor = (
        process_content(to_upper())
        .then(process_content(add_prefix("Processed: ")))
        .then(add_metadata("processed_at", "2025-03-21"))
        .then(add_metadata("processor", "example"))
    )
    result = processor(doc)
    print(f"Processed document: {result}")

    return result


async def example_chainable_operation():
    """Demonstrate using a chainable operation."""
    print("\n=== Chainable Operation Example ===")

    # Create a document
    doc = TextDocument(
        id="doc2",
        content="hello, pepperpy!",
        metadata={"created_at": "2025-03-21"},
    )
    print(f"Original document: {doc}")

    # Create a chainable operation
    operation = (
        create_chainable_operation("document_processor", doc)
        .add_step(process_content(capitalize()))
        .add_step(process_content(add_suffix(" (processed)")))
        .add_step(add_metadata("processed_at", "2025-03-21"))
        .add_step(add_metadata("processor", "chainable_operation"))
        .with_metadata("operation_type", "document_processing")
    )

    # Execute the operation
    result = await operation.execute()
    print(f"Operation result: {result}")

    return result


async def example_complex_composition():
    """Demonstrate complex composition of chainable methods."""
    print("\n=== Complex Composition Example ===")

    # Create a text processor pipeline
    text_processor = (
        create_pipeline("text_processor")
        .add_step(trim())
        .add_step(capitalize())
        .add_step(replace("World", "PepperPy"))
    )

    # Create a document processor that uses the text processor
    doc_processor = (
        create_pipeline("doc_processor")
        .add_step(
            process_content(
                ChainableMethod(
                    lambda text: text_processor.execute(text),
                    name="text_pipeline",
                    description="Process text using a pipeline",
                )
            )
        )
        .add_step(add_metadata("processor", "complex_composition"))
        .add_step(add_metadata("processed_at", "2025-03-21"))
    )

    # Create a document
    doc = TextDocument(
        id="doc3",
        content="  hello, world!  ",
        metadata={"created_at": "2025-03-21"},
    )
    print(f"Original document: {doc}")

    # Process the document
    result = doc_processor.execute(doc)
    print(f"Complex processed document: {result}")

    return result


async def main():
    """Run all examples."""
    print("Chainable API Methods Example")
    print("=============================")

    try:
        # Run the basic chaining example
        await example_basic_chaining()

        # Run the pipeline example
        await example_pipeline()

        # Run the document processing example
        await example_document_processing()

        # Run the chainable operation example
        await example_chainable_operation()

        # Run the complex composition example
        await example_complex_composition()

    except PepperpyError as e:
        logger.error(f"Error in example: {e}")


if __name__ == "__main__":
    asyncio.run(main())
