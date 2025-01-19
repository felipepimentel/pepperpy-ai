"""Base module for text chunking and chunk management."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re


@dataclass
class Chunk:
    """Represents a chunk of text with metadata."""
    
    text: str
    start_index: int
    end_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __len__(self) -> int:
        """Get chunk length."""
        return len(self.text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary format."""
        return {
            "text": self.text,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        """Create chunk from dictionary format."""
        return cls(
            text=data["text"],
            start_index=data["start_index"],
            end_index=data["end_index"],
            metadata=data["metadata"]
        )


class BaseChunker(ABC):
    """Abstract base class for text chunkers."""
    
    @abstractmethod
    def split_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Split text into chunks."""
        pass


class TokenChunker(BaseChunker):
    """Chunks text based on token count."""
    
    def __init__(
        self,
        max_tokens: int = 512,
        overlap_tokens: int = 50
    ) -> None:
        """Initialize token chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk.
            overlap_tokens: Number of tokens to overlap between chunks.
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
    
    def split_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Split text into chunks based on token count.
        
        Args:
            text: Text to split.
            metadata: Optional metadata to add to chunks.
            
        Returns:
            List of chunks.
        """
        # TODO: Implement proper tokenization
        # For now, use words as proxy for tokens
        words = text.split()
        chunks = []
        
        start_idx = 0
        while start_idx < len(words):
            # Get chunk words
            end_idx = min(start_idx + self.max_tokens, len(words))
            chunk_words = words[start_idx:end_idx]
            
            # Create chunk
            chunk = Chunk(
                text=" ".join(chunk_words),
                start_index=start_idx,
                end_index=end_idx,
                metadata=metadata or {}
            )
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start_idx = end_idx - self.overlap_tokens
            if start_idx < 0:
                start_idx = 0
        
        return chunks


class SentenceChunker(BaseChunker):
    """Chunks text based on sentences."""
    
    def __init__(
        self,
        max_sentences: int = 5,
        overlap_sentences: int = 1
    ) -> None:
        """Initialize sentence chunker.
        
        Args:
            max_sentences: Maximum sentences per chunk.
            overlap_sentences: Number of sentences to overlap between chunks.
        """
        self.max_sentences = max_sentences
        self.overlap_sentences = overlap_sentences
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Basic sentence splitting - can be improved
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def split_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Split text into chunks based on sentences.
        
        Args:
            text: Text to split.
            metadata: Optional metadata to add to chunks.
            
        Returns:
            List of chunks.
        """
        sentences = self._split_into_sentences(text)
        chunks = []
        
        start_idx = 0
        while start_idx < len(sentences):
            # Get chunk sentences
            end_idx = min(start_idx + self.max_sentences, len(sentences))
            chunk_sentences = sentences[start_idx:end_idx]
            
            # Create chunk
            chunk = Chunk(
                text=" ".join(chunk_sentences),
                start_index=start_idx,
                end_index=end_idx,
                metadata=metadata or {}
            )
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start_idx = end_idx - self.overlap_sentences
            if start_idx < 0:
                start_idx = 0
        
        return chunks


class ParagraphChunker(BaseChunker):
    """Chunks text based on paragraphs."""
    
    def __init__(
        self,
        max_paragraphs: int = 3,
        overlap_paragraphs: int = 1
    ) -> None:
        """Initialize paragraph chunker.
        
        Args:
            max_paragraphs: Maximum paragraphs per chunk.
            overlap_paragraphs: Number of paragraphs to overlap between chunks.
        """
        self.max_paragraphs = max_paragraphs
        self.overlap_paragraphs = overlap_paragraphs
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]
    
    def split_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Split text into chunks based on paragraphs.
        
        Args:
            text: Text to split.
            metadata: Optional metadata to add to chunks.
            
        Returns:
            List of chunks.
        """
        paragraphs = self._split_into_paragraphs(text)
        chunks = []
        
        start_idx = 0
        while start_idx < len(paragraphs):
            # Get chunk paragraphs
            end_idx = min(start_idx + self.max_paragraphs, len(paragraphs))
            chunk_paragraphs = paragraphs[start_idx:end_idx]
            
            # Create chunk
            chunk = Chunk(
                text="\n\n".join(chunk_paragraphs),
                start_index=start_idx,
                end_index=end_idx,
                metadata=metadata or {}
            )
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start_idx = end_idx - self.overlap_paragraphs
            if start_idx < 0:
                start_idx = 0
        
        return chunks


class ChunkManager:
    """Manages text chunking with different strategies."""
    
    def __init__(self) -> None:
        """Initialize chunk manager."""
        self.chunkers: Dict[str, BaseChunker] = {
            "token": TokenChunker(),
            "sentence": SentenceChunker(),
            "paragraph": ParagraphChunker()
        }
    
    def register_chunker(self, name: str, chunker: BaseChunker) -> None:
        """Register a new chunker.
        
        Args:
            name: Chunker name.
            chunker: Chunker instance.
        """
        self.chunkers[name] = chunker
    
    def get_chunker(self, name: str) -> BaseChunker:
        """Get a registered chunker.
        
        Args:
            name: Chunker name.
            
        Returns:
            Chunker instance.
            
        Raises:
            KeyError: If chunker not found.
        """
        if name not in self.chunkers:
            raise KeyError(f"Chunker '{name}' not found")
        return self.chunkers[name]
    
    def split_text(
        self,
        text: str,
        chunker_name: str = "token",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Split text using specified chunker.
        
        Args:
            text: Text to split.
            chunker_name: Name of chunker to use.
            metadata: Optional metadata to add to chunks.
            
        Returns:
            List of chunks.
        """
        chunker = self.get_chunker(chunker_name)
        return chunker.split_text(text, metadata) 