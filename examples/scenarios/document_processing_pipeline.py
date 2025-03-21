#!/usr/bin/env python
"""Document Processing Pipeline Example for PepperPy.

This example demonstrates a complete document processing pipeline that combines:
1. RAG (Retrieval Augmented Generation)
2. Memory optimization for large documents
3. Caching strategies
4. Performance monitoring
5. Error handling and retries
6. Batch processing
7. Progress tracking

The pipeline processes large documents efficiently while maintaining memory usage
under control and providing detailed metrics about the processing.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from tqdm import tqdm

from pepperpy.core.logging import Logger, LogLevel, setup_logging
from pepperpy.core.monitoring import MetricsCollector, Timer
from pepperpy.errors import PepperpyError
from pepperpy.rag.document import Document, DocumentMetadata
from pepperpy.rag.memory_optimization import (
    DocumentChunk,
    StreamingProcessor,
    create_memory_efficient_document,
    process_document_streaming,
)
from pepperpy.rag.pipeline import (
    Pipeline,
    PipelineContext,
    PipelineStage,
)
from pepperpy.rag.provider import RAGProvider
from pepperpy.rag.providers.local import LocalRAGProvider
from pepperpy.storage.providers.local import LocalStorageProvider
from pepperpy.utils.retry import retry_with_backoff

# Configure logging
setup_logging(level=LogLevel.INFO.value)
logger = Logger.get_logger(__name__)

# Initialize metrics collector
metrics = MetricsCollector()


class DocumentPreprocessor(StreamingProcessor[Dict[str, float], str]):
    """Preprocesses documents in a memory-efficient way."""

    def __init__(self, chunk_size: int = 4096):
        """Initialize the preprocessor.

        Args:
            chunk_size: Size of chunks to process at once
        """
        self.chunk_size = chunk_size
        self.total_words = 0
        self.unique_words = set()

    def process_chunk(self, chunk: DocumentChunk[str]) -> Dict[str, float]:
        """Process a single document chunk.

        Args:
            chunk: Document chunk to process

        Returns:
            Dictionary with chunk statistics
        """
        # Split into words and normalize
        words = chunk.content.lower().split()
        self.total_words += len(words)
        self.unique_words.update(words)

        # Calculate basic statistics
        word_count = len(words)
        unique_count = len(set(words))
        avg_word_length = (
            sum(len(w) for w in words) / word_count if word_count > 0 else 0
        )

        return {
            "word_count": word_count,
            "unique_words": unique_count,
            "avg_word_length": avg_word_length,
            "chunk_id": chunk.index,
        }


class DocumentEnrichmentStage(PipelineStage[Document, Document]):
    """Enriches documents with additional metadata."""

    def __init__(self):
        """Initialize the enrichment stage."""
        self.processed_count = 0

    async def process(self, document: Document, context: PipelineContext) -> Document:
        """Process a single document.

        Args:
            document: Document to enrich
            context: Pipeline context

        Returns:
            Enriched document
        """
        with Timer() as timer:
            # Create memory-efficient document
            efficient_doc = create_memory_efficient_document(
                content=document.content,
                metadata=document.metadata,
            )

            # Process document in chunks
            processor = DocumentPreprocessor(chunk_size=1024 * 64)
            stats = process_document_streaming(
                document=efficient_doc,
                processor=processor,
                chunk_size=1024 * 64,
            )

            # Update document metadata
            document.metadata.update(
                {
                    "total_words": processor.total_words,
                    "unique_words": len(processor.unique_words),
                    "processing_time": timer.elapsed_seconds,
                    "chunk_stats": stats,
                }
            )

            self.processed_count += 1
            metrics.increment("documents_enriched")
            metrics.observe("document_processing_time", timer.elapsed_seconds)

            return document


class DocumentIndexingStage(PipelineStage[Document, Document]):
    """Indexes documents in the RAG provider."""

    def __init__(self, provider: RAGProvider):
        """Initialize the indexing stage.

        Args:
            provider: RAG provider to use for indexing
        """
        self.provider = provider
        self.indexed_count = 0

    @retry_with_backoff(max_attempts=3)
    async def process(self, document: Document, context: PipelineContext) -> Document:
        """Process a single document.

        Args:
            document: Document to index
            context: Pipeline context

        Returns:
            Indexed document
        """
        with Timer() as timer:
            # Index the document
            await self.provider.add_documents([document])

            self.indexed_count += 1
            metrics.increment("documents_indexed")
            metrics.observe("document_indexing_time", timer.elapsed_seconds)

            return document


class DocumentProcessingPipeline:
    """Complete document processing pipeline."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize the pipeline.

        Args:
            storage_dir: Directory for storing processed documents
        """
        # Initialize providers
        self.storage = LocalStorageProvider(
            base_dir=storage_dir or Path("data/documents")
        )
        self.rag_provider = LocalRAGProvider(
            storage=self.storage,
            embedding_dimension=384,
        )

        # Create pipeline stages
        self.enrichment = DocumentEnrichmentStage()
        self.indexing = DocumentIndexingStage(provider=self.rag_provider)

        # Build pipeline
        self.pipeline = Pipeline()
        self.pipeline.add_stage(self.enrichment)
        self.pipeline.add_stage(self.indexing)

    async def process_documents(self, documents: List[Document]) -> List[Document]:
        """Process a batch of documents.

        Args:
            documents: List of documents to process

        Returns:
            List of processed documents
        """
        logger.info(f"Processing {len(documents)} documents...")

        try:
            # Initialize providers
            await self.rag_provider.initialize()

            # Process documents through pipeline
            processed = []
            with tqdm(total=len(documents), desc="Processing") as pbar:
                async for doc in self.pipeline.process_many(documents):
                    processed.append(doc)
                    pbar.update(1)

            # Log statistics
            logger.info(
                f"Processed {len(processed)} documents:\n"
                f"- Enriched: {self.enrichment.processed_count}\n"
                f"- Indexed: {self.indexing.indexed_count}"
            )

            return processed

        finally:
            # Cleanup
            await self.rag_provider.shutdown()


async def main():
    """Run the document processing example."""
    # Create sample documents
    documents = []
    for i in range(5):
        # Create a document with random content
        content = " ".join(
            np.random.choice(
                ["document", "processing", "example", "pepperpy", "test"],
                size=1000,
            )
        )
        metadata = DocumentMetadata(
            id=f"doc_{i}",
            source="example",
            title=f"Document {i}",
        )
        documents.append(Document(content=content, metadata=metadata))

    # Create temporary directory for storage
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize pipeline
        pipeline = DocumentProcessingPipeline(storage_dir=Path(temp_dir))

        # Process documents
        try:
            processed = await pipeline.process_documents(documents)

            # Print metrics
            print("\nProcessing Metrics:")
            for metric in metrics.get_metrics():
                print(f"- {metric.name}: {metric.value}")

        except PepperpyError as e:
            logger.error(f"Error processing documents: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
