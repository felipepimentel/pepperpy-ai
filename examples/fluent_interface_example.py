#!/usr/bin/env python
"""Example demonstrating fluent interface patterns for complex operations.

This example shows how to use the fluent interface patterns provided by the
PepperPy framework to create readable and chainable APIs for complex operations.

Purpose:
    Demonstrate how to use fluent interfaces for complex operations in PepperPy.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install -e .

    2. Run the example:
       python examples/fluent_interface_example.py
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List

# Import directly from the module since the fluent module is new
# and may not be exposed in the public API yet
from pepperpy.core.fluent import (
    FluentBuilder,
    FluentChain,
    FluentOperation,
    create_builder,
    create_chain,
)
from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Document:
    """Simple document class for demonstration purposes."""

    id: str
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class DocumentBuilder(FluentBuilder[Document]):
    """Builder for Document objects using fluent interface."""

    def __init__(self, document_id: str):
        """Initialize the document builder.

        Args:
            document_id: The ID of the document to build
        """
        super().__init__(f"document_{document_id}")
        self._config["id"] = document_id
        self._config["title"] = ""
        self._config["content"] = ""
        self._config["metadata"] = {}

    def with_title(self, title: str) -> "DocumentBuilder":
        """Set the document title.

        Args:
            title: The title of the document

        Returns:
            Self for method chaining
        """
        self._config["title"] = title
        return self

    def with_content(self, content: str) -> "DocumentBuilder":
        """Set the document content.

        Args:
            content: The content of the document

        Returns:
            Self for method chaining
        """
        self._config["content"] = content
        return self

    def with_metadata_item(self, key: str, value: Any) -> "DocumentBuilder":
        """Add a metadata item to the document.

        Args:
            key: The metadata key
            value: The metadata value

        Returns:
            Self for method chaining
        """
        self._config["metadata"][key] = value
        return self

    def _build_internal(self) -> Document:
        """Build the document.

        Returns:
            The built document
        """
        return Document(
            id=self._config["id"],
            title=self._config["title"],
            content=self._config["content"],
            metadata=self._config["metadata"],
        )


class DocumentProcessor(FluentOperation[Document]):
    """Processor for documents using fluent interface."""

    def __init__(self, document: Document):
        """Initialize the document processor.

        Args:
            document: The document to process
        """
        super().__init__(f"processor_{document.id}")
        self._document = document
        self._transformations = []

    def transform_title(self, transformer: callable) -> "DocumentProcessor":
        """Add a title transformation.

        Args:
            transformer: A function that transforms the title

        Returns:
            Self for method chaining
        """

        def transform():
            self._document.title = transformer(self._document.title)

        self._transformations.append(transform)
        return self

    def transform_content(self, transformer: callable) -> "DocumentProcessor":
        """Add a content transformation.

        Args:
            transformer: A function that transforms the content

        Returns:
            Self for method chaining
        """

        def transform():
            self._document.content = transformer(self._document.content)

        self._transformations.append(transform)
        return self

    def add_metadata(self, key: str, value: Any) -> "DocumentProcessor":
        """Add metadata to the document.

        Args:
            key: The metadata key
            value: The metadata value

        Returns:
            Self for method chaining
        """

        def transform():
            self._document.metadata[key] = value

        self._transformations.append(transform)
        return self

    async def execute(self) -> Document:
        """Execute all transformations on the document.

        Returns:
            The processed document
        """
        for transform in self._transformations:
            transform()

        return self._document


class DocumentPipeline(FluentChain[List[Document]]):
    """Pipeline for processing multiple documents using fluent interface."""

    def __init__(self, name: str):
        """Initialize the document pipeline.

        Args:
            name: The name of the pipeline
        """
        super().__init__(name)
        self._documents = []
        self._processors = []

    def add_document(self, document: Document) -> "DocumentPipeline":
        """Add a document to the pipeline.

        Args:
            document: The document to add

        Returns:
            Self for method chaining
        """
        self._documents.append(document)
        return self

    def add_processor(self, processor_factory: callable) -> "DocumentPipeline":
        """Add a processor to the pipeline.

        Args:
            processor_factory: A function that creates a processor for a document

        Returns:
            Self for method chaining
        """
        self._processors.append(processor_factory)
        return self

    async def execute(self) -> List[Document]:
        """Execute the pipeline on all documents.

        Returns:
            The processed documents
        """
        results = []

        for document in self._documents:
            current_doc = document
            for processor_factory in self._processors:
                processor = processor_factory(current_doc)
                current_doc = await processor.execute()
            results.append(current_doc)

        return results


async def example_document_builder():
    """Demonstrate the DocumentBuilder fluent interface."""
    print("\n=== Document Builder Example ===")

    # Create a document using the fluent builder
    document = (
        DocumentBuilder("doc1")
        .with_title("Sample Document")
        .with_content("This is a sample document created using a fluent builder.")
        .with_metadata_item("author", "PepperPy")
        .with_metadata_item("created_at", "2025-03-21")
        .build()
    )

    print(f"Created document: {document.id}")
    print(f"Title: {document.title}")
    print(f"Content: {document.content}")
    print(f"Metadata: {document.metadata}")

    return document


async def example_document_processor(document: Document):
    """Demonstrate the DocumentProcessor fluent interface."""
    print("\n=== Document Processor Example ===")

    # Process a document using the fluent processor
    processed_document = await (
        DocumentProcessor(document)
        .transform_title(lambda title: title.upper())
        .transform_content(lambda content: content.replace("sample", "processed"))
        .add_metadata("processed_at", "2025-03-21")
        .execute()
    )

    print(f"Processed document: {processed_document.id}")
    print(f"Title: {processed_document.title}")
    print(f"Content: {processed_document.content}")
    print(f"Metadata: {processed_document.metadata}")

    return processed_document


async def example_document_pipeline():
    """Demonstrate the DocumentPipeline fluent interface."""
    print("\n=== Document Pipeline Example ===")

    # Create multiple documents
    doc1 = (
        DocumentBuilder("doc1")
        .with_title("Document 1")
        .with_content("Content 1")
        .build()
    )
    doc2 = (
        DocumentBuilder("doc2")
        .with_title("Document 2")
        .with_content("Content 2")
        .build()
    )
    doc3 = (
        DocumentBuilder("doc3")
        .with_title("Document 3")
        .with_content("Content 3")
        .build()
    )

    # Create a pipeline to process all documents
    processed_documents = await (
        DocumentPipeline("sample_pipeline")
        .add_document(doc1)
        .add_document(doc2)
        .add_document(doc3)
        .add_processor(
            lambda doc: DocumentProcessor(doc)
            .transform_title(lambda title: f"Processed: {title}")
            .add_metadata("pipeline", "sample_pipeline")
        )
        .add_processor(
            lambda doc: DocumentProcessor(doc).transform_content(
                lambda content: f"{content} (processed)"
            )
        )
        .execute()
    )

    for doc in processed_documents:
        print(f"Pipeline processed document: {doc.id}")
        print(f"Title: {doc.title}")
        print(f"Content: {doc.content}")
        print(f"Metadata: {doc.metadata}")
        print()

    return processed_documents


async def example_generic_builder():
    """Demonstrate the generic builder fluent interface."""
    print("\n=== Generic Builder Example ===")

    # Create a configuration using the generic builder
    config = (
        create_builder("config_builder")
        .with_config("name", "sample_config")
        .with_config("version", "1.0.0")
        .with_config("settings", {"debug": True, "timeout": 30})
        .with_metadata({"created_by": "example", "purpose": "demonstration"})
        .build()
    )

    print(f"Created configuration: {config}")
    print(f"Settings: {config.get('settings')}")
    print(f"Metadata: {config.get('metadata')}")

    return config


async def example_generic_chain():
    """Demonstrate the generic chain fluent interface."""
    print("\n=== Generic Chain Example ===")

    # Define some operations
    def operation1(input_value):
        print(f"Operation 1: Processing {input_value}")
        return {"result1": f"Processed {input_value}"}

    def operation2(result1):
        print(f"Operation 2: Processing {result1}")
        return {"result2": f"Further processed {result1}"}

    def operation3(result2):
        print(f"Operation 3: Processing {result2}")
        return f"Final result: {result2}"

    # Create a chain of operations
    result = await (
        create_chain("sample_chain")
        .with_input("input_value", "initial data")
        .with_operation(operation1)
        .with_operation(operation2)
        .with_operation(operation3)
        .execute()
    )

    print(f"Chain result: {result}")

    return result


async def main():
    """Run all examples."""
    print("Fluent Interface Patterns Example")
    print("=================================")

    try:
        # Run the document builder example
        document = await example_document_builder()

        # Run the document processor example
        processed_document = await example_document_processor(document)

        # Run the document pipeline example
        await example_document_pipeline()

        # Run the generic builder example
        await example_generic_builder()

        # Run the generic chain example
        await example_generic_chain()

    except PepperpyError as e:
        logger.error(f"Error in example: {e}")


if __name__ == "__main__":
    asyncio.run(main())
