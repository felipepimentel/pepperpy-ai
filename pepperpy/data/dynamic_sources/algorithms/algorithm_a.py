"""Text chunking algorithm implementation."""

import logging
from typing import Any, Dict, List, Optional

from ....common.errors import PepperpyError
from .base_algorithm import BaseAlgorithm, AlgorithmError


logger = logging.getLogger(__name__)


class ChunkingError(PepperpyError):
    """Chunking error."""
    pass


class TextChunkingAlgorithm(BaseAlgorithm):
    """Text chunking algorithm implementation."""
    
    def __init__(
        self,
        name: str,
        chunk_size: int,
        overlap: int = 0,
        min_chunk_size: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize algorithm.
        
        Args:
            name: Algorithm name
            chunk_size: Maximum chunk size
            overlap: Overlap between chunks (default: 0)
            min_chunk_size: Optional minimum chunk size
            config: Optional algorithm configuration
        """
        super().__init__(name, config)
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._min_chunk_size = min_chunk_size
        
    def _validate_input(self, data: Any) -> None:
        """Validate input data.
        
        Args:
            data: Data to validate
            
        Raises:
            AlgorithmError: If data is invalid
        """
        if not isinstance(data, str):
            raise AlgorithmError(f"Expected string input, got {type(data)}")
            
    def _validate_output(self, data: Any) -> None:
        """Validate output data.
        
        Args:
            data: Data to validate
            
        Raises:
            AlgorithmError: If data is invalid
        """
        if not isinstance(data, list):
            raise AlgorithmError(f"Expected list output, got {type(data)}")
            
        if not all(isinstance(chunk, str) for chunk in data):
            raise AlgorithmError("All chunks must be strings")
            
    async def _process_data(
        self,
        data: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Process text into chunks.
        
        Args:
            data: Text to process
            context: Optional processing context
            
        Returns:
            List of text chunks
            
        Raises:
            AlgorithmError: If text cannot be processed
        """
        try:
            # Split into chunks
            chunks = []
            start = 0
            
            while start < len(data):
                # Get chunk
                end = start + self._chunk_size
                chunk = data[start:end]
                
                # Add if meets minimum size
                if (
                    self._min_chunk_size is None
                    or len(chunk) >= self._min_chunk_size
                ):
                    chunks.append(chunk)
                    
                # Move to next chunk
                start = end - self._overlap
                
            return chunks
            
        except Exception as e:
            raise ChunkingError(f"Failed to chunk text: {e}") from e
            
    def validate(self) -> None:
        """Validate algorithm state."""
        super().validate()
        
        if self._chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
            
        if self._overlap < 0:
            raise ValueError("Overlap must be non-negative")
            
        if self._overlap >= self._chunk_size:
            raise ValueError("Overlap must be less than chunk size")
            
        if self._min_chunk_size is not None:
            if self._min_chunk_size <= 0:
                raise ValueError("Minimum chunk size must be positive")
                
            if self._min_chunk_size > self._chunk_size:
                raise ValueError(
                    "Minimum chunk size must not exceed maximum chunk size"
                )
