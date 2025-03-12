"""Advanced document chunking strategies for RAG.

This module provides advanced chunking strategies for RAG document processing,
including configurable overlaps, semantic chunking, and hierarchical chunking.
These strategies help improve retrieval quality by creating more meaningful
document chunks.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pepperpy.core.telemetry import get_provider_telemetry
from pepperpy.types.common import Document, Metadata

# Set up telemetry
telemetry = get_provider_telemetry("rag_chunking")


class ChunkingStrategy(Enum):
    """Strategies for chunking documents."""

    FIXED_SIZE = "fixed_size"  # Fixed-size chunks with optional overlap
    SENTENCE = "sentence"  # Sentence-based chunking
    PARAGRAPH = "paragraph"  # Paragraph-based chunking
    SEMANTIC = "semantic"  # Semantic-based chunking using embeddings
    HIERARCHICAL = "hierarchical"  # Hierarchical chunking (nested chunks)
    SLIDING_WINDOW = "sliding_window"  # Sliding window with configurable stride
    CUSTOM = "custom"  # Custom chunking using a provided function


@dataclass
class ChunkingConfig:
    """Configuration for document chunking.

    This class defines the configuration for document chunking, including
    chunk size, overlap, and strategy-specific parameters.
    """

    strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    chunk_size: int = 1000  # Default chunk size in characters or tokens
    chunk_overlap: int = 200  # Default overlap between chunks
    separator: str = " "  # Separator to use when joining text
    keep_separator: bool = True  # Whether to keep separators in chunks
    respect_sentence_boundaries: bool = True  # Try to avoid breaking sentences
    respect_paragraph_boundaries: bool = True  # Try to avoid breaking paragraphs
    min_chunk_size: int = 100  # Minimum chunk size to avoid tiny chunks
    max_chunk_size: Optional[int] = None  # Maximum chunk size (None = no limit)
    custom_chunker: Optional[Callable[[str, "ChunkingConfig"], List[str]]] = None
    metadata_config: Dict[str, Any] = field(
        default_factory=dict
    )  # Config for metadata extraction


class ChunkMetadata(Dict[str, Any]):
    """Metadata for a document chunk.

    This class represents metadata for a document chunk, including position
    information, relationships to other chunks, and content-specific metadata.
    """

    @property
    def chunk_index(self) -> int:
        """Get the index of this chunk in the document."""
        return self.get("chunk_index", 0)

    @property
    def total_chunks(self) -> int:
        """Get the total number of chunks in the document."""
        return self.get("total_chunks", 1)

    @property
    def parent_id(self) -> Optional[str]:
        """Get the ID of the parent document."""
        return self.get("parent_id")

    @property
    def next_chunk_id(self) -> Optional[str]:
        """Get the ID of the next chunk in sequence."""
        return self.get("next_chunk_id")

    @property
    def prev_chunk_id(self) -> Optional[str]:
        """Get the ID of the previous chunk in sequence."""
        return self.get("prev_chunk_id")

    @property
    def hierarchy_level(self) -> int:
        """Get the hierarchy level of this chunk (for hierarchical chunking)."""
        return self.get("hierarchy_level", 0)

    @property
    def is_summary(self) -> bool:
        """Check if this chunk is a summary chunk."""
        return self.get("is_summary", False)


def chunk_document(
    document: Document, config: Optional[ChunkingConfig] = None
) -> List[Document]:
    """Chunk a document according to the specified strategy.

    This function chunks a document according to the specified strategy,
    creating multiple smaller documents with appropriate metadata.

    Args:
        document: The document to chunk.
        config: Optional configuration for chunking. If not provided,
            default configuration is used.

    Returns:
        A list of chunked documents.
    """
    if config is None:
        config = ChunkingConfig()

    telemetry.info(
        "chunk_document_started",
        f"Chunking document with strategy {config.strategy.value}",
        {"document_id": document.id, "strategy": config.strategy.value},
    )

    # Extract text from the document
    text = document.content

    # Choose chunking strategy
    if config.strategy == ChunkingStrategy.FIXED_SIZE:
        chunks = _chunk_fixed_size(text, config)
    elif config.strategy == ChunkingStrategy.SENTENCE:
        chunks = _chunk_by_sentence(text, config)
    elif config.strategy == ChunkingStrategy.PARAGRAPH:
        chunks = _chunk_by_paragraph(text, config)
    elif config.strategy == ChunkingStrategy.SEMANTIC:
        chunks = _chunk_semantic(text, config)
    elif config.strategy == ChunkingStrategy.HIERARCHICAL:
        chunks = _chunk_hierarchical(text, config)
    elif config.strategy == ChunkingStrategy.SLIDING_WINDOW:
        chunks = _chunk_sliding_window(text, config)
    elif config.strategy == ChunkingStrategy.CUSTOM and config.custom_chunker:
        chunks = config.custom_chunker(text, config)
    else:
        # Default to fixed size if strategy is not recognized
        chunks = _chunk_fixed_size(text, config)

    # Create documents from chunks
    chunked_docs = []
    for i, chunk_text in enumerate(chunks):
        # Create metadata for the chunk
        chunk_metadata = {}
        if document.metadata:
            # Copy existing metadata
            for key, value in document.metadata.to_dict().items():
                chunk_metadata[key] = value

        # Add chunk-specific metadata
        chunk_metadata.update({
            "chunk_index": i,
            "total_chunks": len(chunks),
            "parent_id": document.id,
            "strategy": config.strategy.value,
        })

        # Add next/prev chunk IDs
        if i > 0:
            chunk_metadata["prev_chunk_id"] = f"{document.id}_chunk_{i - 1}"
        if i < len(chunks) - 1:
            chunk_metadata["next_chunk_id"] = f"{document.id}_chunk_{i + 1}"

        # Create the chunked document
        chunk_id = f"{document.id}_chunk_{i}"
        chunked_doc = Document(
            id=chunk_id,
            content=chunk_text,
            metadata=Metadata.from_dict(chunk_metadata),
        )
        chunked_docs.append(chunked_doc)

    telemetry.info(
        "chunk_document_completed",
        f"Document chunked into {len(chunked_docs)} chunks",
        {"document_id": document.id, "chunk_count": len(chunked_docs)},
    )

    return chunked_docs


def _chunk_fixed_size(text: str, config: ChunkingConfig) -> List[str]:
    """Chunk text into fixed-size chunks with configurable overlap.

    Args:
        text: The text to chunk.
        config: Configuration for chunking.

    Returns:
        A list of text chunks.
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate end position
        end = start + config.chunk_size

        # Adjust end position if needed
        if end < text_length and config.respect_sentence_boundaries:
            # Try to find a sentence boundary
            sentence_end = _find_sentence_boundary(text, end)
            if sentence_end > start + config.min_chunk_size:
                end = sentence_end

        # Ensure we don't exceed text length
        end = min(end, text_length)

        # Extract the chunk
        chunk = text[start:end]
        chunks.append(chunk)

        # Calculate next start position with overlap
        start = end - config.chunk_overlap

        # Ensure we make progress
        if start <= 0 or start >= text_length:
            break

    return chunks


def _chunk_by_sentence(text: str, config: ChunkingConfig) -> List[str]:
    """Chunk text by sentences, combining sentences into chunks of appropriate size.

    Args:
        text: The text to chunk.
        config: Configuration for chunking.

    Returns:
        A list of text chunks.
    """
    if not text:
        return []

    # Split text into sentences
    sentences = _split_into_sentences(text)

    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence_size = len(sentence)

        # If adding this sentence would exceed max_chunk_size, finalize the current chunk
        if (
            config.max_chunk_size
            and current_size > 0
            and current_size + sentence_size > config.max_chunk_size
        ):
            chunks.append(config.separator.join(current_chunk))
            current_chunk = []
            current_size = 0

        # Add the sentence to the current chunk
        current_chunk.append(sentence)
        current_size += sentence_size

        # If we've reached or exceeded the target chunk size, finalize the chunk
        if current_size >= config.chunk_size:
            chunks.append(config.separator.join(current_chunk))
            current_chunk = []
            current_size = 0

    # Add any remaining content as the final chunk
    if current_chunk:
        chunks.append(config.separator.join(current_chunk))

    return chunks


def _chunk_by_paragraph(text: str, config: ChunkingConfig) -> List[str]:
    """Chunk text by paragraphs, combining paragraphs into chunks of appropriate size.

    Args:
        text: The text to chunk.
        config: Configuration for chunking.

    Returns:
        A list of text chunks.
    """
    if not text:
        return []

    # Split text into paragraphs
    paragraphs = _split_into_paragraphs(text)

    chunks = []
    current_chunk = []
    current_size = 0

    for paragraph in paragraphs:
        paragraph_size = len(paragraph)

        # If this paragraph alone exceeds max_chunk_size, chunk it by sentence
        if config.max_chunk_size and paragraph_size > config.max_chunk_size:
            # If we have content in the current chunk, finalize it
            if current_chunk:
                chunks.append(config.separator.join(current_chunk))
                current_chunk = []
                current_size = 0

            # Chunk this paragraph by sentence and add each as a separate chunk
            paragraph_chunks = _chunk_by_sentence(paragraph, config)
            chunks.extend(paragraph_chunks)
            continue

        # If adding this paragraph would exceed max_chunk_size, finalize the current chunk
        if (
            config.max_chunk_size
            and current_size > 0
            and current_size + paragraph_size > config.max_chunk_size
        ):
            chunks.append(config.separator.join(current_chunk))
            current_chunk = []
            current_size = 0

        # Add the paragraph to the current chunk
        current_chunk.append(paragraph)
        current_size += paragraph_size

        # If we've reached or exceeded the target chunk size, finalize the chunk
        if current_size >= config.chunk_size:
            chunks.append(config.separator.join(current_chunk))
            current_chunk = []
            current_size = 0

    # Add any remaining content as the final chunk
    if current_chunk:
        chunks.append(config.separator.join(current_chunk))

    return chunks


def _chunk_sliding_window(text: str, config: ChunkingConfig) -> List[str]:
    """Chunk text using a sliding window approach with configurable stride.

    Args:
        text: The text to chunk.
        config: Configuration for chunking.

    Returns:
        A list of text chunks.
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)
    stride = config.chunk_size - config.chunk_overlap

    while start < text_length:
        # Calculate end position
        end = start + config.chunk_size

        # Ensure we don't exceed text length
        end = min(end, text_length)

        # Extract the chunk
        chunk = text[start:end]
        chunks.append(chunk)

        # Move the window by the stride
        start += stride

        # Ensure we make progress
        if stride <= 0:
            break

    return chunks


def _chunk_semantic(text: str, config: ChunkingConfig) -> List[str]:
    """Chunk text based on semantic boundaries using embeddings.

    This is a placeholder implementation. In a real implementation, this would
    use embeddings to identify semantic boundaries in the text.

    Args:
        text: The text to chunk.
        config: Configuration for chunking.

    Returns:
        A list of text chunks.
    """
    # For now, fall back to paragraph-based chunking
    telemetry.warning(
        "semantic_chunking_fallback",
        "Semantic chunking not fully implemented, falling back to paragraph chunking",
    )
    return _chunk_by_paragraph(text, config)


def _chunk_hierarchical(text: str, config: ChunkingConfig) -> List[str]:
    """Create hierarchical chunks with multiple levels of granularity.

    This creates both large chunks for context and smaller chunks for detailed retrieval.
    The hierarchy is encoded in the chunk metadata.

    Args:
        text: The text to chunk.
        config: Configuration for chunking.

    Returns:
        A list of text chunks.
    """
    # For now, just create regular chunks
    # In a real implementation, this would create multiple levels of chunks
    telemetry.warning(
        "hierarchical_chunking_fallback",
        "Hierarchical chunking not fully implemented, falling back to fixed-size chunking",
    )
    return _chunk_fixed_size(text, config)


def _find_sentence_boundary(text: str, position: int) -> int:
    """Find the nearest sentence boundary after the given position.

    Args:
        text: The text to search.
        position: The position to start searching from.

    Returns:
        The position of the nearest sentence boundary.
    """
    # Look for sentence-ending punctuation followed by whitespace or end of text
    sentence_end_pattern = r"[.!?][\s]"

    # Search for the pattern after the given position
    match = re.search(sentence_end_pattern, text[position : position + 100])
    if match:
        return position + match.end()

    # If no sentence boundary found, look for any whitespace
    whitespace_match = re.search(r"\s", text[position : position + 50])
    if whitespace_match:
        return position + whitespace_match.end()

    # If no boundary found, return the original position
    return position


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences.

    Args:
        text: The text to split.

    Returns:
        A list of sentences.
    """
    # Simple sentence splitting - in a real implementation, this would be more sophisticated
    sentence_pattern = r"(?<=[.!?])\s+"
    sentences = re.split(sentence_pattern, text)
    return [s.strip() for s in sentences if s.strip()]


def _split_into_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs.

    Args:
        text: The text to split.

    Returns:
        A list of paragraphs.
    """
    # Split on double newlines or more
    paragraph_pattern = r"\n\s*\n"
    paragraphs = re.split(paragraph_pattern, text)
    return [p.strip() for p in paragraphs if p.strip()]


class ChunkingPipeline:
    """Pipeline for chunking documents with multiple strategies.

    This class provides a pipeline for chunking documents with multiple
    strategies, allowing for more complex chunking workflows.
    """

    def __init__(self, strategies: List[Tuple[ChunkingStrategy, ChunkingConfig]]):
        """Initialize the chunking pipeline.

        Args:
            strategies: A list of (strategy, config) tuples to apply in sequence.
        """
        self.strategies = strategies

    def process(self, document: Document) -> List[Document]:
        """Process a document through the chunking pipeline.

        Args:
            document: The document to process.

        Returns:
            A list of chunked documents.
        """
        documents = [document]

        for strategy, config in self.strategies:
            config.strategy = strategy
            new_documents = []

            for doc in documents:
                chunks = chunk_document(doc, config)
                new_documents.extend(chunks)

            documents = new_documents

        return documents


# Convenience functions


def create_fixed_size_chunker(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    respect_sentence_boundaries: bool = True,
) -> Callable[[Document], List[Document]]:
    """Create a fixed-size chunker with the specified parameters.

    Args:
        chunk_size: The size of each chunk in characters.
        chunk_overlap: The overlap between chunks in characters.
        respect_sentence_boundaries: Whether to respect sentence boundaries.

    Returns:
        A function that chunks documents using the fixed-size strategy.
    """
    config = ChunkingConfig(
        strategy=ChunkingStrategy.FIXED_SIZE,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        respect_sentence_boundaries=respect_sentence_boundaries,
    )

    def chunker(document: Document) -> List[Document]:
        return chunk_document(document, config)

    return chunker


def create_sentence_chunker(
    target_chunk_size: int = 1000, max_chunk_size: Optional[int] = 1500
) -> Callable[[Document], List[Document]]:
    """Create a sentence-based chunker with the specified parameters.

    Args:
        target_chunk_size: The target size of each chunk in characters.
        max_chunk_size: The maximum size of each chunk in characters.

    Returns:
        A function that chunks documents using the sentence-based strategy.
    """
    config = ChunkingConfig(
        strategy=ChunkingStrategy.SENTENCE,
        chunk_size=target_chunk_size,
        max_chunk_size=max_chunk_size,
    )

    def chunker(document: Document) -> List[Document]:
        return chunk_document(document, config)

    return chunker


def create_paragraph_chunker(
    target_chunk_size: int = 1000, max_chunk_size: Optional[int] = 1500
) -> Callable[[Document], List[Document]]:
    """Create a paragraph-based chunker with the specified parameters.

    Args:
        target_chunk_size: The target size of each chunk in characters.
        max_chunk_size: The maximum size of each chunk in characters.

    Returns:
        A function that chunks documents using the paragraph-based strategy.
    """
    config = ChunkingConfig(
        strategy=ChunkingStrategy.PARAGRAPH,
        chunk_size=target_chunk_size,
        max_chunk_size=max_chunk_size,
    )

    def chunker(document: Document) -> List[Document]:
        return chunk_document(document, config)

    return chunker


def create_sliding_window_chunker(
    window_size: int = 1000, stride: int = 500
) -> Callable[[Document], List[Document]]:
    """Create a sliding window chunker with the specified parameters.

    Args:
        window_size: The size of the sliding window in characters.
        stride: The stride (step size) of the sliding window in characters.

    Returns:
        A function that chunks documents using the sliding window strategy.
    """
    config = ChunkingConfig(
        strategy=ChunkingStrategy.SLIDING_WINDOW,
        chunk_size=window_size,
        chunk_overlap=window_size - stride,
    )

    def chunker(document: Document) -> List[Document]:
        return chunk_document(document, config)

    return chunker


def create_custom_chunker(
    chunker_func: Callable[[str, ChunkingConfig], List[str]],
    config: Optional[ChunkingConfig] = None,
) -> Callable[[Document], List[Document]]:
    """Create a custom chunker with the specified function.

    Args:
        chunker_func: A function that takes text and config and returns chunks.
        config: Optional configuration for chunking.

    Returns:
        A function that chunks documents using the custom function.
    """
    if config is None:
        config = ChunkingConfig()

    config.strategy = ChunkingStrategy.CUSTOM
    config.custom_chunker = chunker_func

    def chunker(document: Document) -> List[Document]:
        return chunk_document(document, config)

    return chunker
