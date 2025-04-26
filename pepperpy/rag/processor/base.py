"""Base classes for text processing in RAG."""

from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar
import numpy as np

from pepperpy.core.errors import DomainError
from pepperpy.plugin import ProviderPlugin


class TextProcessingError(DomainError):
    """Error raised during text processing."""
    
    def __init__(
        self,
        message: str,
        *args,
        processor: str | None = None,
        **kwargs,
    ):
        """Initialize text processing error.
        
        Args:
            message: Error message
            *args: Additional positional arguments
            processor: Processor that raised the error
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, domain="rag.processor", **kwargs)
        self.processor = processor


class ProcessingOptions:
    """Options for text processing."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        split_by_paragraph: bool = True,
        preserve_newlines: bool = False,
        **kwargs: Any,
    ):
        """Initialize processing options.
        
        Args:
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks in characters
            split_by_paragraph: Whether to split by paragraph first
            preserve_newlines: Whether to preserve newlines in the output
            **kwargs: Additional options
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.split_by_paragraph = split_by_paragraph
        self.preserve_newlines = preserve_newlines
        
        # Store additional options
        for key, value in kwargs.items():
            setattr(self, key, value)


class ProcessedText:
    """Result of text processing."""
    
    def __init__(
        self,
        chunks: List[str],
        tokens: Optional[List[List[str]]] = None,
        sentences: Optional[List[List[str]]] = None,
        embeddings: Optional[List[np.ndarray]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize processed text.
        
        Args:
            chunks: List of text chunks
            tokens: Optional list of tokens for each chunk
            sentences: Optional list of sentences for each chunk
            embeddings: Optional list of embeddings for each chunk
            metadata: Optional metadata about the processing
        """
        self.chunks = chunks
        self.tokens = tokens or []
        self.sentences = sentences or []
        self.embeddings = embeddings or []
        self.metadata = metadata or {}


class TextProcessor(Protocol):
    """Interface for text processors."""
    
    async def initialize(self) -> None:
        """Initialize processor resources."""
        ...
        
    async def cleanup(self) -> None:
        """Clean up processor resources."""
        ...
        
    async def process_text(
        self, text: str, options: Optional[ProcessingOptions] = None
    ) -> ProcessedText:
        """Process text into chunks with optional metadata.
        
        Args:
            text: Text to process
            options: Processing options
            
        Returns:
            Processed text with chunks and metadata
            
        Raises:
            TextProcessingError: If processing fails
        """
        ...
        
    async def process_batch(
        self, texts: List[str], options: Optional[ProcessingOptions] = None
    ) -> List[ProcessedText]:
        """Process a batch of texts.
        
        Args:
            texts: List of texts to process
            options: Processing options
            
        Returns:
            List of processed texts
            
        Raises:
            TextProcessingError: If processing fails
        """
        ...
        
    def chunk_text(
        self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[str]:
        """Split text into chunks.
        
        Args:
            text: Text to split
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks in characters
            
        Returns:
            List of text chunks
        """
        ... 