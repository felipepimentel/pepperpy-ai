"""Base module for retrieval augmented generation (RAG)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import json
import os

from pepperpy.data_stores.chunking import Chunk, ChunkManager
from pepperpy.llms.base_llm import BaseLLM
from pepperpy.llms.types import LLMResponse


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