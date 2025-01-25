"""Text processing tools.

This module provides tools for text processing operations like
chunking, summarization, and formatting.
"""

from typing import Any, Dict, Optional, List

from .base import BaseTool, ToolConfig
from ..providers.base import BaseProvider


class TextChunkerTool(BaseTool):
    """Tool for chunking text into smaller pieces."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 100,
        dependencies: Optional[Dict[str, BaseProvider]] = None,
    ) -> None:
        """Initialize text chunker tool.
        
        Args:
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
            dependencies: Optional tool dependencies
        """
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if overlap < 0:
            raise ValueError("Overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("Overlap must be less than chunk size")
            
        config = ToolConfig(
            name="text_chunker",
            description="Split text into overlapping chunks",
            parameters={
                "chunk_size": chunk_size,
                "overlap": overlap,
            },
            metadata={
                "version": "1.0.0",
                "type": "text_processor",
            },
        )
        super().__init__(config, dependencies)
        self._chunk_size = chunk_size
        self._overlap = overlap
    
    async def _setup(self) -> None:
        """Set up chunker resources."""
        # No special setup needed
        pass
    
    async def _teardown(self) -> None:
        """Clean up chunker resources."""
        # No special cleanup needed
        pass
    
    async def _validate_impl(self) -> None:
        """Validate chunker state.
        
        Raises:
            ValueError: If configuration is invalid.
        """
        if self._chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if self._overlap < 0:
            raise ValueError("Overlap must be non-negative")
        if self._overlap >= self._chunk_size:
            raise ValueError("Overlap must be less than chunk size")
    
    async def _execute_impl(
        self,
        input_data: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Split text into chunks.
        
        Args:
            input_data: Input text to chunk
            context: Optional execution context
            
        Returns:
            List of text chunks
            
        Raises:
            ValueError: If input is not a string
        """
        if not isinstance(input_data, str):
            raise ValueError("Input must be a string")
            
        if not input_data:
            return []
            
        # Get parameters from context or use defaults
        chunk_size = context.get("chunk_size", self._chunk_size) if context else self._chunk_size
        overlap = context.get("overlap", self._overlap) if context else self._overlap
        
        # Validate parameters
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if overlap < 0:
            raise ValueError("Overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("Overlap must be less than chunk size")
            
        # Split text into chunks
        chunks = []
        start = 0
        text_len = len(input_data)
        
        while start < text_len:
            # Calculate end position
            end = min(start + chunk_size, text_len)
            
            # If not at the end, try to break at a space
            if end < text_len:
                # Look for last space within chunk
                while end > start and not input_data[end - 1].isspace():
                    end -= 1
                if end == start:
                    # No space found, use hard break
                    end = min(start + chunk_size, text_len)
            
            # Add chunk
            chunks.append(input_data[start:end].strip())
            
            # Move start position for next chunk
            start = end - overlap
        
        return chunks 