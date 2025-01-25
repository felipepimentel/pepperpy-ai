"""Text processing tools module."""

from typing import Any, Dict, List, Optional

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.persistence.storage.chunking import Chunk


class TextChunkerError(PepperpyError):
    """Text chunker error."""
    pass


class TextChunkerTool:
    """Text chunker tool.
    
    This tool provides text chunking functionality.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize text chunker tool.
        
        Args:
            config: Optional configuration dictionary
        """
        self._config = config or {}
        self._is_initialized = False
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get tool configuration."""
        return self._config
    
    @property
    def is_initialized(self) -> bool:
        """Check if tool is initialized."""
        return self._is_initialized
    
    async def initialize(self) -> None:
        """Initialize tool.
        
        This method should be called before using the tool.
        """
        self._is_initialized = True
    
    async def cleanup(self) -> None:
        """Clean up tool.
        
        This method should be called when the tool is no longer needed.
        """
        self._is_initialized = False
    
    async def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """Split text into chunks.
        
        Args:
            text: Text to split
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
            metadata: Optional metadata to add to chunks
            
        Returns:
            List of chunks
            
        Raises:
            TextChunkerError: If chunking fails
        """
        if not self.is_initialized:
            raise TextChunkerError("Tool not initialized")
        
        if not text:
            raise TextChunkerError("Text cannot be empty")
        
        if chunk_size <= 0:
            raise TextChunkerError("Chunk size must be positive")
        
        if overlap < 0:
            raise TextChunkerError("Overlap must be non-negative")
        
        if overlap >= chunk_size:
            raise TextChunkerError("Overlap must be less than chunk size")
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Get chunk text
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # Create chunk
            chunk = Chunk(
                text=chunk_text,
                metadata=metadata or {},
            )
            chunks.append(chunk)
            
            # Move to next chunk
            start = end - overlap
        
        return chunks 