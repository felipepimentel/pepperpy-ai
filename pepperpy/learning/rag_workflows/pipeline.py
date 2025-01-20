"""Base module for retrieval augmented generation (RAG)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Protocol, Sequence
import json
import os
from datetime import datetime

from pepperpy.data_stores.chunking import Chunk, ChunkManager
from pepperpy.llms.base_llm import BaseLLM
from pepperpy.llms.types import LLMResponse
from pepperpy.common.errors import RAGError, ConfigurationError
from pepperpy.monitoring.performance_metrics import MetricsCollector


@dataclass
class Document:
    """Represents a document with metadata."""
    
    content: str
    doc_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[Chunk] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary format."""
        return {
            "content": self.content,
            "doc_id": self.doc_id,
            "metadata": self.metadata,
            "chunks": [chunk.to_dict() for chunk in self.chunks]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create document from dictionary format."""
        return cls(
            content=data["content"],
            doc_id=data["doc_id"],
            metadata=data["metadata"],
            chunks=[Chunk.from_dict(chunk) for chunk in data["chunks"]]
        )


class BaseVectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def add_embeddings(
        self,
        texts: List[str],
        metadata: List[Dict[str, Any]]
    ) -> None:
        """Add embeddings to store."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.0
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar texts."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all embeddings."""
        pass


class SimpleVectorStore(BaseVectorStore):
    """Simple in-memory vector store using cosine similarity."""
    
    def __init__(self, llm: BaseLLM) -> None:
        """Initialize vector store.
        
        Args:
            llm: LLM for generating embeddings.
        """
        self.llm = llm
        self.embeddings: List[List[float]] = []
        self.texts: List[str] = []
        self.metadata: List[Dict[str, Any]] = []
    
    async def add_embeddings(
        self,
        texts: List[str],
        metadata: List[Dict[str, Any]]
    ) -> None:
        """Add embeddings to store.
        
        Args:
            texts: List of texts to embed.
            metadata: List of metadata for each text.
        """
        # Get embeddings from LLM
        for text, meta in zip(texts, metadata):
            embedding = await self.llm.get_embedding(text)
            self.embeddings.append(embedding)
            self.texts.append(text)
            self.metadata.append(meta)
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.0
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar texts.
        
        Args:
            query: Query text.
            limit: Maximum number of results.
            min_score: Minimum similarity score.
            
        Returns:
            List of (text, score, metadata) tuples.
        """
        # Get query embedding
        query_embedding = await self.llm.get_embedding(query)
        
        # Calculate similarities
        similarities = []
        for i, embedding in enumerate(self.embeddings):
            score = self._cosine_similarity(query_embedding, embedding)
            if score >= min_score:
                similarities.append((self.texts[i], score, self.metadata[i]))
        
        # Sort by score
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:limit]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        return dot_product / (norm_a * norm_b)
    
    async def clear(self) -> None:
        """Clear all embeddings."""
        self.embeddings.clear()
        self.texts.clear()
        self.metadata.clear()


class RAGManager:
    """Manages retrieval augmented generation."""
    
    def __init__(
        self,
        llm: BaseLLM,
        vector_store: Optional[BaseVectorStore] = None,
        chunk_manager: Optional[ChunkManager] = None
    ) -> None:
        """Initialize RAG manager.
        
        Args:
            llm: LLM for text generation and embeddings.
            vector_store: Optional vector store.
            chunk_manager: Optional chunk manager.
        """
        self.llm = llm
        self.vector_store = vector_store or SimpleVectorStore(llm)
        self.chunk_manager = chunk_manager or ChunkManager()
        self.documents: Dict[str, Document] = {}
    
    async def add_document(
        self,
        content: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunker_name: str = "paragraph"
    ) -> None:
        """Add a document to the knowledge base.
        
        Args:
            content: Document content.
            doc_id: Document ID.
            metadata: Optional document metadata.
            chunker_name: Name of chunker to use.
        """
        # Create document
        doc = Document(
            content=content,
            doc_id=doc_id,
            metadata=metadata or {}
        )
        
        # Split into chunks
        doc.chunks = self.chunk_manager.split_text(
            content,
            chunker_name=chunker_name,
            metadata={"doc_id": doc_id, **(metadata or {})}
        )
        
        # Add to vector store
        await self.vector_store.add_embeddings(
            texts=[chunk.text for chunk in doc.chunks],
            metadata=[chunk.metadata for chunk in doc.chunks]
        )
        
        # Store document
        self.documents[doc_id] = doc
    
    async def query(
        self,
        query: str,
        num_chunks: int = 3,
        min_score: float = 0.7
    ) -> List[Tuple[Chunk, float]]:
        """Query the knowledge base.
        
        Args:
            query: Query text.
            num_chunks: Number of chunks to retrieve.
            min_score: Minimum similarity score.
            
        Returns:
            List of (chunk, score) tuples.
        """
        # Search vector store
        results = await self.vector_store.search(
            query,
            limit=num_chunks,
            min_score=min_score
        )
        
        # Convert to chunks
        chunks = []
        for text, score, metadata in results:
            doc = self.documents[metadata["doc_id"]]
            chunk = next(
                chunk for chunk in doc.chunks
                if chunk.text == text
            )
            chunks.append((chunk, score))
        
        return chunks
    
    async def generate_with_context(
        self,
        query: str,
        prompt_template: str,
        num_chunks: int = 3,
        min_score: float = 0.7
    ) -> LLMResponse:
        """Generate text using retrieved context.
        
        Args:
            query: Query text.
            prompt_template: Template for prompt with {context} and {query}.
            num_chunks: Number of chunks to retrieve.
            min_score: Minimum similarity score.
            
        Returns:
            Generated text response.
        """
        # Get relevant chunks
        chunks = await self.query(
            query,
            num_chunks=num_chunks,
            min_score=min_score
        )
        
        if not chunks:
            # No relevant context found
            return await self.llm.generate(query)
        
        # Format context
        context = "\n\n".join(
            f"[Score: {score:.2f}] {chunk.text}"
            for chunk, score in chunks
        )
        
        # Generate with context
        prompt = prompt_template.format(
            context=context,
            query=query
        )
        
        return await self.llm.generate(prompt)
    
    async def save_documents(self, path: str) -> None:
        """Save documents to file.
        
        Args:
            path: Path to save file.
        """
        data = {
            doc_id: doc.to_dict()
            for doc_id, doc in self.documents.items()
        }
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    async def load_documents(self, path: str) -> None:
        """Load documents from file.
        
        Args:
            path: Path to load file.
        """
        with open(path, "r") as f:
            data = json.load(f)
            
        self.documents = {
            doc_id: Document.from_dict(doc_data)
            for doc_id, doc_data in data.items()
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.vector_store.clear()
        self.documents.clear()


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline."""
    
    max_context_length: int = 2000
    min_similarity: float = 0.7
    batch_size: int = 5
    enable_metrics: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if self.max_context_length <= 0:
            raise ConfigurationError("max_context_length must be positive")
        if not 0 <= self.min_similarity <= 1:
            raise ConfigurationError("min_similarity must be between 0 and 1")
        if self.batch_size <= 0:
            raise ConfigurationError("batch_size must be positive")


@dataclass
class RetrievalResult:
    """Result from the retrieval step."""
    content: str
    metadata: Dict[str, Any]
    score: float
    source_id: str
    retrieved_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score,
            "source_id": self.source_id,
            "retrieved_at": self.retrieved_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievalResult":
        """Create from dictionary format."""
        if "retrieved_at" in data:
            data["retrieved_at"] = datetime.fromisoformat(data["retrieved_at"])
        return cls(**data)


class Retriever(Protocol):
    """Protocol for retrieval components."""
    async def retrieve(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Retrieve relevant content.
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of retrieval results
            
        Raises:
            RAGError: If retrieval fails
        """
        ...


class Generator(Protocol):
    """Protocol for generation components."""
    async def generate(
        self,
        prompt: str,
        context: List[RetrievalResult],
        **kwargs: Any
    ) -> str:
        """Generate response using retrieved context.
        
        Args:
            prompt: Input prompt
            context: Retrieved context
            **kwargs: Additional generation parameters
            
        Returns:
            Generated response
            
        Raises:
            RAGError: If generation fails
        """
        ...


class RAGPipeline:
    """Manages the RAG workflow pipeline."""
    
    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
        config: Optional[RAGConfig] = None,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        """Initialize RAG pipeline.
        
        Args:
            retriever: Component for retrieving relevant content
            generator: Component for generating responses
            config: Optional pipeline configuration
            metrics_collector: Optional metrics collector
            
        Raises:
            ConfigurationError: If invalid configuration provided
        """
        self.retriever = retriever
        self.generator = generator
        self.config = config or RAGConfig()
        self.metrics_collector = metrics_collector
        
    async def _collect_metrics(
        self,
        operation: str,
        start_time: datetime,
        **metrics: Any
    ) -> None:
        """Collect operation metrics if enabled."""
        if self.config.enable_metrics and self.metrics_collector:
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self.metrics_collector.record_metrics(
                operation=operation,
                duration=duration,
                **metrics
            )
        
    async def process(
        self,
        query: str,
        k: Optional[int] = None,
        filter: Optional[Dict[str, Any]] = None,
        **generation_kwargs: Any
    ) -> Dict[str, Any]:
        """Process a query through the RAG pipeline.
        
        Args:
            query: Input query
            k: Optional number of results to retrieve (defaults to batch_size)
            filter: Optional metadata filter
            **generation_kwargs: Additional generation parameters
            
        Returns:
            Dict containing:
                - response: Generated response
                - context: Retrieved context
                - metadata: Processing metadata
                
        Raises:
            RAGError: If processing fails
            ValueError: If query is empty
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")
            
        try:
            start_time = datetime.utcnow()
            
            # Retrieve relevant context
            k = k or self.config.batch_size
            context = await self.retriever.retrieve(
                query=query,
                k=k,
                filter=filter
            )
            
            await self._collect_metrics(
                operation="retrieval",
                start_time=start_time,
                num_results=len(context)
            )
            
            # Filter and limit context length
            filtered_context = []
            total_length = 0
            
            for result in context:
                length = len(result.content)
                if total_length + length <= self.config.max_context_length:
                    filtered_context.append(result)
                    total_length += length
                else:
                    break
                    
            # Generate response
            generation_start = datetime.utcnow()
            response = await self.generator.generate(
                prompt=query,
                context=filtered_context,
                **generation_kwargs
            )
            
            await self._collect_metrics(
                operation="generation",
                start_time=generation_start,
                context_length=total_length
            )
            
            result = {
                "response": response,
                "context": filtered_context,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "num_context": len(filtered_context),
                    "total_context_length": total_length,
                    "processing_time": (datetime.utcnow() - start_time).total_seconds()
                }
            }
            
            await self._collect_metrics(
                operation="pipeline",
                start_time=start_time,
                total_context=len(filtered_context)
            )
            
            return result
            
        except Exception as e:
            raise RAGError(f"RAG pipeline processing failed: {str(e)}") from e
            
    async def batch_process(
        self,
        queries: List[str],
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Process multiple queries through the RAG pipeline.
        
        Args:
            queries: List of input queries
            **kwargs: Additional processing parameters
            
        Returns:
            List of processing results
            
        Raises:
            RAGError: If batch processing fails
            ValueError: If queries list is empty
        """
        if not queries:
            raise ValueError("Queries list cannot be empty")
            
        try:
            start_time = datetime.utcnow()
            results = []
            
            for query in queries:
                result = await self.process(query, **kwargs)
                results.append(result)
                
            await self._collect_metrics(
                operation="batch_process",
                start_time=start_time,
                num_queries=len(queries)
            )
            
            return results
            
        except Exception as e:
            raise RAGError(f"RAG pipeline batch processing failed: {str(e)}") from e
            
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.metrics_collector:
            await self.metrics_collector.flush() 