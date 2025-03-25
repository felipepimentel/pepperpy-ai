"""Chroma vector store provider for RAG capabilities.

This module provides a ChromaDB-based implementation of the RAG provider interface,
supporting vector storage and retrieval for RAG operations.

Example:
    >>> from pepperpy.rag import RAGProvider
    >>> provider = RAGProvider.from_config({
    ...     "provider": "chroma",
    ...     "path": "./chroma_db"
    ... })
    >>> await provider.add_documents([
    ...     Document(content="Example document", metadata={"source": "test"})
    ... ])
    >>> results = await provider.search("query", top_k=3)
"""

import logging
import os
from typing import Any, Dict, List, Optional, Sequence, cast

from pepperpy.core.utils.imports import lazy_provider_class, import_provider
from pepperpy.rag.base import (
    BaseProvider as RAGProvider,
    Document,
    RAGError,
    SearchResult
)

logger = logging.getLogger(__name__)

@lazy_provider_class('rag', 'chroma')
class ChromaProvider(RAGProvider):
    """ChromaDB implementation of the RAG provider interface.
    
    This provider supports:
    - Persistent vector storage
    - Similarity search
    - Metadata filtering
    - Batch operations
    """

    name = "chroma"

    def __init__(
        self,
        path: Optional[str] = None,
        collection_name: str = "pepperpy",
        embedding_function: Optional[Any] = None,
        **kwargs: Any
    ) -> None:
        """Initialize ChromaDB provider.
        
        Args:
            path: Path to ChromaDB persistence directory
            collection_name: Name of the collection to use
            embedding_function: Optional custom embedding function
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        
        # Import chromadb only when provider is instantiated
        chromadb = import_provider('chromadb', 'rag', 'chroma')
        
        self.path = path
        self.collection_name = collection_name
        self._embedding_function = embedding_function
        
        # Initialize client with persistence if path provided
        if path:
            os.makedirs(path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=path)
        else:
            self.client = chromadb.Client()
            
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function
        )
        
    async def add_documents(
        self,
        documents: Sequence[Document],
        **kwargs: Any
    ) -> List[str]:
        """Add documents to the vector store.
        
        Args:
            documents: Sequence of documents to add
            **kwargs: Additional options
            
        Returns:
            List of document IDs
            
        Raises:
            RAGError: If adding documents fails
        """
        try:
            # Prepare document batches
            ids = [str(doc.id) for doc in documents]  # Ensure IDs are strings
            texts = [doc.content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            
            return ids
        except Exception as e:
            raise RAGError(f"Failed to add documents: {str(e)}")
            
    async def search(
        self,
        query: str,
        top_k: int = 3,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> List[SearchResult]:
        """Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter: Optional metadata filter
            **kwargs: Additional search options
            
        Returns:
            List of search results
            
        Raises:
            RAGError: If search fails
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filter
            )
            
            search_results = []
            for i, (doc_id, text, metadata, distance) in enumerate(zip(
                results['ids'][0],
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                search_results.append(
                    SearchResult(
                        document=Document(
                            id=doc_id,
                            content=text,
                            metadata=metadata
                        ),
                        score=1.0 - distance,  # Convert distance to similarity score
                        rank=i + 1
                    )
                )
                
            return search_results
        except Exception as e:
            raise RAGError(f"Search failed: {str(e)}")
            
    async def delete_documents(
        self,
        document_ids: List[str],
        **kwargs: Any
    ) -> None:
        """Delete documents from the vector store.
        
        Args:
            document_ids: List of document IDs to delete
            **kwargs: Additional options
            
        Raises:
            RAGError: If deletion fails
        """
        try:
            self.collection.delete(ids=document_ids)
        except Exception as e:
            raise RAGError(f"Failed to delete documents: {str(e)}")
            
    async def get_document(
        self,
        document_id: str,
        **kwargs: Any
    ) -> Optional[Document]:
        """Get a document by ID.
        
        Args:
            document_id: Document ID to retrieve
            **kwargs: Additional options
            
        Returns:
            Document if found, None otherwise
            
        Raises:
            RAGError: If retrieval fails
        """
        try:
            result = self.collection.get(ids=[document_id])
            
            if not result['ids']:
                return None
                
            return Document(
                id=result['ids'][0],
                content=result['documents'][0],
                metadata=result['metadatas'][0]
            )
        except Exception as e:
            raise RAGError(f"Failed to get document: {str(e)}")
            
    async def clear(self, **kwargs: Any) -> None:
        """Clear all documents from the vector store.
        
        Args:
            **kwargs: Additional options
            
        Raises:
            RAGError: If clearing fails
        """
        try:
            self.collection.delete()
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_function
            )
        except Exception as e:
            raise RAGError(f"Failed to clear vector store: {str(e)}")
            
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics
        """
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "provider": self.name,
                "collection": self.collection_name,
                "persistent": bool(self.path)
            }
        except Exception as e:
            logger.warning(f"Failed to get stats: {str(e)}")
            return {
                "document_count": 0,
                "provider": self.name,
                "collection": self.collection_name,
                "persistent": bool(self.path)
            } 