"""Example demonstrating the content module functionality.

This example shows how to:
1. Create and manage text content
2. Process text content with different operations
3. Analyze text content for metrics
4. Store and retrieve content using local storage
"""

from tempfile import TemporaryDirectory

from pepperpy.content import (
    LocalContentStorage,
    TextAnalyzer,
    TextContent,
    TextProcessor,
)


def main():
    """Run the content example."""
    # Create some sample text content
    text = """
    The Pepperpy framework provides powerful tools for managing and processing content.
    It supports different content types, including text and files.
    The content module offers features like:
    - Content loading and validation
    - Content transformation
    - Content storage and retrieval
    - Content metadata management
    """
    content = TextContent("sample", text.strip())
    print(f"Created text content: {content.name}")
    print(f"Content size: {content.metadata.size} bytes")
    print("\nOriginal text:")
    print(content.load())

    # Process the text content
    processor = TextProcessor()
    processed = processor.process(content, operations=["strip", "normalize", "lower"])
    print("\nProcessed text:")
    print(processed.load())

    # Analyze the text content
    analyzer = TextAnalyzer()
    metrics = analyzer.process(
        content, metrics=["length", "words", "sentences", "avg_word_length"]
    )
    print("\nText analysis:")
    for metric, value in metrics.items():
        print(f"- {metric}: {value}")

    # Store and retrieve content
    with TemporaryDirectory() as temp_dir:
        storage = LocalContentStorage(temp_dir)

        # Save the content
        content_id = storage.save(content)
        print(f"\nSaved content with ID: {content_id}")

        # List available content
        stored = storage.list()
        print("\nStored content:")
        for id_, metadata in stored.items():
            print(f"- {metadata.name} ({metadata.type.name})")

        # Load the content back
        loaded = storage.load(content_id)
        print("\nLoaded text:")
        print(loaded.load())

        # Clean up
        storage.delete(content_id)
        print("\nDeleted content")


if __name__ == "__main__":
    main()
