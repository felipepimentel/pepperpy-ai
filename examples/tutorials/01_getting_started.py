#!/usr/bin/env python
"""Getting Started with PepperPy.

This tutorial introduces the basic concepts and features of PepperPy:
1. Document handling and RAG
2. Memory optimization
3. Logging and monitoring
4. Error handling

By the end of this tutorial, you'll understand:
- How to create and process documents
- How to use memory-efficient data structures
- How to set up logging and monitoring
- How to handle errors properly
"""

import asyncio
from pathlib import Path
from typing import Dict, List

from pepperpy.core.logging import Logger, LogLevel, setup_logging
from pepperpy.core.monitoring import MetricsCollector
from pepperpy.errors import PepperpyError
from pepperpy.rag.document import Document, DocumentMetadata
from pepperpy.rag.memory_optimization import create_memory_efficient_document
from pepperpy.storage.providers.local import LocalStorageProvider

# Step 1: Configure logging
setup_logging(level=LogLevel.INFO.value)
logger = Logger.get_logger(__name__)

# Step 2: Initialize metrics
metrics = MetricsCollector()


def create_sample_documents() -> List[Document]:
    """Create sample documents for the tutorial.

    Returns:
        List of sample documents
    """
    # Create documents with different content types
    documents = [
        Document(
            content="This is a simple text document for testing.",
            metadata=DocumentMetadata(
                id="doc1",
                source="tutorial",
                title="Simple Text",
                content_type="text/plain",
            ),
        ),
        Document(
            content="<html><body>This is an HTML document.</body></html>",
            metadata=DocumentMetadata(
                id="doc2",
                source="tutorial",
                title="HTML Document",
                content_type="text/html",
            ),
        ),
        Document(
            content='{"key": "This is a JSON document"}',
            metadata=DocumentMetadata(
                id="doc3",
                source="tutorial",
                title="JSON Document",
                content_type="application/json",
            ),
        ),
    ]

    logger.info(f"Created {len(documents)} sample documents")
    return documents


def process_document(document: Document) -> Dict[str, int]:
    """Process a single document and collect statistics.

    Args:
        document: Document to process

    Returns:
        Dictionary with document statistics
    """
    try:
        # Create memory-efficient version
        efficient_doc = create_memory_efficient_document(
            content=document.content,
            metadata=document.metadata,
        )

        # Calculate basic statistics
        words = efficient_doc.content.split()
        unique_words = set(words)

        # Collect metrics
        metrics.increment("documents_processed")
        metrics.observe("document_word_count", len(words))

        return {
            "total_words": len(words),
            "unique_words": len(unique_words),
            "avg_word_length": sum(len(w) for w in words) / len(words),
        }

    except Exception as e:
        # Log error and re-raise
        logger.error(f"Error processing document {document.metadata.id}: {e}")
        raise PepperpyError(f"Document processing failed: {e}") from e


async def store_documents(
    documents: List[Document],
    storage_dir: Path,
) -> None:
    """Store documents using the local storage provider.

    Args:
        documents: List of documents to store
        storage_dir: Directory for storage
    """
    try:
        # Initialize storage provider
        storage = LocalStorageProvider(base_dir=storage_dir)

        # Store each document
        for doc in documents:
            await storage.store_document(doc)
            logger.info(f"Stored document {doc.metadata.id}")
            metrics.increment("documents_stored")

    except Exception as e:
        logger.error(f"Error storing documents: {e}")
        raise PepperpyError(f"Storage operation failed: {e}") from e


async def main():
    """Run the getting started tutorial."""
    logger.info("Starting PepperPy tutorial...")

    try:
        # Step 1: Create sample documents
        documents = create_sample_documents()

        # Step 2: Process each document
        for doc in documents:
            logger.info(f"Processing document: {doc.metadata.title}")
            stats = process_document(doc)
            logger.info(f"Document statistics: {stats}")

        # Step 3: Store documents
        storage_dir = Path("data/tutorial")
        storage_dir.mkdir(parents=True, exist_ok=True)

        await store_documents(documents, storage_dir)

        # Step 4: Print metrics
        logger.info("\nProcessing metrics:")
        for metric in metrics.get_metrics():
            logger.info(f"- {metric.name}: {metric.value}")

    except PepperpyError as e:
        logger.error(f"Tutorial failed: {e}")
        raise

    logger.info("Tutorial completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
