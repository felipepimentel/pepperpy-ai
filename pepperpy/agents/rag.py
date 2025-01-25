"""RAG agent implementation."""

import logging
from typing import Any, Dict, List, Optional, cast, Sequence

from ..common.errors import PepperpyError
from ..providers.embeddings.base import BaseEmbeddingProvider
from ..providers.vector_store.base import BaseVectorStoreProvider
from ..providers.retriever.base import BaseRetrieverProvider
from .base import BaseAgent


logger = logging.getLogger(__name__)


class RAGAgentError(PepperpyError):
    """RAG agent error class."""
    pass


class RAGAgent(BaseAgent):
    """RAG (Retrieval-Augmented Generation) agent implementation."""
    
    def __init__(
        self,
        name: str,
        llm: Any,
        capabilities: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize RAG agent.
        
        Args:
            name: Agent name.
            llm: LLM provider instance.
            capabilities: Agent capabilities.
            config: Optional agent configuration.
            
        Raises:
            RAGAgentError: If initialization fails.
        """
        super().__init__(name, llm, capabilities, config)
        
        # Initialize RAG components
        self._embeddings = cast(Optional[BaseEmbeddingProvider], capabilities.get("embeddings"))
        self._vector_store = cast(Optional[BaseVectorStoreProvider], capabilities.get("vector_store"))
        self._retriever = cast(Optional[BaseRetrieverProvider], capabilities.get("retriever"))
        
        # Get RAG configuration
        self._max_chunks = config.get("max_chunks", 5) if config else 5
        self._chunk_size = config.get("chunk_size", 1000) if config else 1000
        self._overlap = config.get("overlap", 100) if config else 100
        
        if self._max_chunks <= 0:
            raise RAGAgentError("Max chunks must be positive")
        if self._chunk_size <= 0:
            raise RAGAgentError("Chunk size must be positive")
        if self._overlap < 0:
            raise RAGAgentError("Overlap must be non-negative")
        if self._overlap >= self._chunk_size:
            raise RAGAgentError("Overlap must be less than chunk size")
    
    async def _setup(self) -> None:
        """Set up RAG agent resources.
        
        Raises:
            RAGAgentError: If setup fails.
        """
        try:
            # Initialize embeddings provider
            if self._embeddings:
                await self._embeddings.initialize()
            
            # Initialize vector store
            if self._vector_store:
                await self._vector_store.initialize()
            
            # Initialize retriever
            if self._retriever:
                await self._retriever.initialize()
        except Exception as e:
            raise RAGAgentError(f"Failed to set up RAG agent: {e}")
    
    async def _teardown(self) -> None:
        """Clean up RAG agent resources.
        
        Raises:
            RAGAgentError: If cleanup fails.
        """
        try:
            # Clean up embeddings provider
            if self._embeddings:
                await self._embeddings.cleanup()
            
            # Clean up vector store
            if self._vector_store:
                await self._vector_store.cleanup()
            
            # Clean up retriever
            if self._retriever:
                await self._retriever.cleanup()
        except Exception as e:
            raise RAGAgentError(f"Failed to clean up RAG agent: {e}")
    
    async def _validate_impl(self) -> None:
        """Validate RAG agent state.
        
        Raises:
            RAGAgentError: If validation fails.
        """
        try:
            if self._max_chunks <= 0:
                raise RAGAgentError("Max chunks must be positive")
            if self._chunk_size <= 0:
                raise RAGAgentError("Chunk size must be positive")
            if self._overlap < 0:
                raise RAGAgentError("Overlap must be non-negative")
            if self._overlap >= self._chunk_size:
                raise RAGAgentError("Overlap must be less than chunk size")
            
            # Validate required capabilities
            if not self._embeddings:
                raise RAGAgentError("Embeddings provider not configured")
            if not self._vector_store:
                raise RAGAgentError("Vector store not configured")
            if not self._retriever:
                raise RAGAgentError("Retriever not configured")
            
            # Validate provider states
            if not self._embeddings.is_initialized:
                raise RAGAgentError("Embeddings provider not initialized")
            if not self._vector_store.is_initialized:
                raise RAGAgentError("Vector store not initialized")
            if not self._retriever.is_initialized:
                raise RAGAgentError("Retriever not initialized")
        except Exception as e:
            raise RAGAgentError(f"Failed to validate RAG agent: {e}")
    
    async def execute(self, input_data: Any) -> Any:
        """Execute RAG agent with input data.
        
        Args:
            input_data: Input data for agent execution.
            
        Returns:
            Agent execution result.
            
        Raises:
            RAGAgentError: If execution fails.
        """
        if not isinstance(input_data, str):
            raise RAGAgentError("Input must be a string")
        
        # Validate state before execution
        await self._validate_impl()
        
        try:
            # Generate query embedding
            query_embedding = await self._embeddings.embed_text(input_data)  # type: ignore
            if not isinstance(query_embedding, list) or not all(isinstance(x, float) for x in query_embedding):
                raise RAGAgentError("Invalid embedding format")
            
            # Retrieve relevant chunks
            chunks = await self._vector_store.search(  # type: ignore
                cast(List[float], query_embedding),
                k=self._max_chunks
            )
            
            # Build context from chunks
            context = "\n\n".join(chunk["text"] for chunk in chunks)
            
            # Generate response with context
            prompt = f"""Context: {context}

Question: {input_data}

Answer based on the context above:"""
            
            response = await self.llm.generate(prompt)
            return response
            
        except Exception as e:
            raise RAGAgentError(f"Failed to execute RAG agent: {e}")
    
    async def add_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add document to RAG knowledge base.
        
        Args:
            text: Document text.
            metadata: Optional document metadata.
            
        Raises:
            RAGAgentError: If document addition fails.
        """
        if not isinstance(text, str):
            raise RAGAgentError("Document must be a string")
        
        # Validate state before adding document
        await self._validate_impl()
        
        try:
            # Generate embeddings for text chunks
            chunks = self._chunk_text(text)
            embeddings = await self._embeddings.embed_text(chunks)  # type: ignore
            if not isinstance(embeddings, list) or not all(isinstance(x, list) and all(isinstance(y, float) for y in x) for x in embeddings):
                raise RAGAgentError("Invalid embeddings format")
            
            # Store chunks with embeddings
            for chunk, embedding in zip(chunks, embeddings):
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata["text"] = chunk
                
                await self._vector_store.add_vectors(  # type: ignore
                    cast(List[List[float]], [embedding]),
                    [chunk_metadata]
                )
        except Exception as e:
            raise RAGAgentError(f"Failed to add document: {e}")
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks.
        
        Args:
            text: Text to split.
            
        Returns:
            List of text chunks.
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            # Calculate end position
            end = min(start + self._chunk_size, text_len)
            
            # If not at the end, try to break at a space
            if end < text_len:
                # Look for last space within chunk
                while end > start and not text[end - 1].isspace():
                    end -= 1
                if end == start:
                    # No space found, use hard break
                    end = min(start + self._chunk_size, text_len)
            
            # Add chunk
            chunks.append(text[start:end].strip())
            
            # Move start position for next chunk
            start = end - self._overlap
        
        return chunks 