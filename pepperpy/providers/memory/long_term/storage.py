"""Memory integration with data stores."""

from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast, Dict, List, Optional, Union
import json
import os
from pathlib import Path

from pepperpy.persistence.storage.document import DocumentMetadata, DocumentStore
from pepperpy.providers.embedding import EmbeddingManager
from pepperpy.providers.vector_store import BaseVectorDB, Document, SearchResult

from ...common.errors import PepperpyError
from ...models.types import Message
from ..base import BaseMemory, MemoryBackend


logger = logging.getLogger(__name__)


class MemoryError(PepperpyError):
    """Memory error."""
    pass


class MemoryIntegration:
    """Integrates memory management with data stores."""

    def __init__(
        self,
        vector_db: BaseVectorDB,
        document_store: DocumentStore,
        embedding_manager: EmbeddingManager,
    ) -> None:
        """Initialize memory integration.

        Args:
            vector_db: Vector database for semantic search
            document_store: Document store for content
            embedding_manager: Embedding manager for vectors
        """
        self.vector_db = vector_db
        self.document_store = document_store
        self.embedding_manager = embedding_manager

    async def add_to_memory(
        self, texts: str | Sequence[str], metadata: dict[str, Any] | None = None
    ) -> str | list[str]:
        """Add text(s) to memory.

        Args:
            texts: Text or list of texts to add
            metadata: Optional metadata for the texts

        Returns:
            Document ID(s)

        Raises:
            Exception: If addition fails
        """
        # Convert to list and ensure all texts are strings
        single_text = isinstance(texts, str)
        texts_list = [str(texts)] if single_text else [str(t) for t in texts]
        metadata_list = [metadata or {}] * len(texts_list)

        # Generate embeddings
        embeddings = await self.embedding_manager.get_embeddings(texts_list)
        embeddings_list = cast(list[list[float]], embeddings)

        # Store documents with metadata and embeddings
        doc_ids = []
        for i, (text, meta, emb) in enumerate(
            zip(texts_list, metadata_list, embeddings_list, strict=True)
        ):
            doc_id = f"mem_{i}"  # TODO: Better ID generation
            doc_ids.append(doc_id)

            # Create document metadata
            doc_metadata = DocumentMetadata(
                id=doc_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                source=meta.get("source", "memory") if meta else "memory",
                tags=meta.get("tags", []) if meta else [],
                embedding=emb,
            )

            # Store in document store
            await self.document_store.store(doc_id, text, doc_metadata)

            # Store in vector database
            doc = Document(
                id=doc_id,
                text=text,  # text is already str from texts_list
                metadata=meta or {},
                embedding=emb,
            )
            await self.vector_db.add_documents([doc])

        return doc_ids[0] if single_text else doc_ids

    async def search_memory(
        self,
        query: str,
        k: int = 5,
        filter: dict[str, Any] | None = None,
        full_documents: bool = True,
    ) -> list[SearchResult] | list[Document]:
        """Search memory for relevant content.

        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter
            full_documents: Whether to return full documents

        Returns:
            Search results or documents

        Raises:
            Exception: If search fails
        """
        # Get query embedding
        query_embedding = await self.embedding_manager.get_embeddings(query)
        query_embedding_list = cast(list[float], query_embedding)

        # Search vector database
        results = await self.vector_db.search(
            query_embedding=query_embedding_list, k=k, filter=filter
        )

        if not full_documents:
            return results

        # Get full documents
        documents = []
        for result in results:
            doc_content, doc_metadata = await self.document_store.retrieve(
                result.document.id
            )
            if doc_content is not None and doc_metadata is not None:
                doc = Document(
                    id=doc_metadata.id,
                    text=cast(str, doc_content),
                    metadata={"similarity_score": result.score},
                    embedding=doc_metadata.embedding,
                )
                documents.append(doc)

        return documents

    async def forget(self, document_ids: str | Sequence[str]) -> None:
        """Remove content from memory.

        Args:
            document_ids: ID(s) to remove

        Raises:
            Exception: If removal fails
        """
        # Convert to list
        ids_list = (
            [document_ids] if isinstance(document_ids, str) else list(document_ids)
        )

        # Delete from both stores
        for doc_id in ids_list:
            await self.document_store.delete(doc_id)
        await self.vector_db.delete(ids_list)

    async def merge_memories(
        self, source_ids: list[str], strategy: str = "concatenate"
    ) -> str:
        """Merge multiple memories into one.

        Args:
            source_ids: IDs of memories to merge
            strategy: Merging strategy ("concatenate" or "summarize")

        Returns:
            ID of the merged memory

        Raises:
            Exception: If merging fails
        """
        # Get source documents
        documents = []
        for doc_id in source_ids:
            doc_content, doc_metadata = await self.document_store.retrieve(doc_id)
            if doc_content is not None and doc_metadata is not None:
                documents.append(cast(str, doc_content))

        if not documents:
            raise ValueError("No valid documents to merge")

        # Merge based on strategy
        if strategy == "concatenate":
            merged_text = "\n\n".join(documents)
        elif strategy == "summarize":
            # TODO: Implement summarization
            raise NotImplementedError("Summarization not implemented yet")
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")

        # Create merged document
        merged_id = await self.add_to_memory(
            merged_text, metadata={"source_ids": source_ids, "merge_strategy": strategy}
        )

        # Cast to str since we know we're adding a single document
        return cast(str, merged_id)

    async def optimize_memory(
        self, max_size: int | None = None, min_relevance: float | None = None
    ) -> None:
        """Optimize memory by removing or consolidating content.

        Args:
            max_size: Optional maximum number of documents to keep
            min_relevance: Optional minimum relevance score to keep

        Raises:
            Exception: If optimization fails
        """
        try:
            # Get all documents with their relevance scores
            # Empty query for general relevance
            query_embedding = await self.embedding_manager.get_embeddings("")
            query_embedding_list = cast(list[float], query_embedding)

            results = await self.vector_db.search(
                query_embedding=query_embedding_list,
                k=max_size or 1000000,  # Large number if no max_size
            )

            # Sort by relevance score
            sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

            # Filter by minimum relevance if specified
            if min_relevance is not None:
                sorted_results = [r for r in sorted_results if r.score >= min_relevance]

            # Trim to max size if specified
            if max_size is not None and len(sorted_results) > max_size:
                to_remove = sorted_results[max_size:]
                # Remove excess documents
                for result in to_remove:
                    await self.forget(result.document.id)

            # Attempt to consolidate similar documents
            if len(sorted_results) > 1:
                clusters = self._cluster_similar_documents(sorted_results)
                for cluster in clusters:
                    if len(cluster) > 1:
                        # Merge documents in each cluster
                        await self.merge_memories(
                            source_ids=[doc.id for doc in cluster],
                            strategy="concatenate",
                        )

        except Exception as e:
            raise Exception(f"Memory optimization failed: {e!s}") from e

    def _cluster_similar_documents(
        self, results: list[SearchResult], similarity_threshold: float = 0.8
    ) -> list[list[Document]]:
        """Cluster similar documents together.

        Args:
            results: Search results to cluster
            similarity_threshold: Minimum similarity score to group documents

        Returns:
            List of document clusters
        """
        # TODO: Implement clustering logic
        return [[doc.document for doc in results]]

    async def cleanup(self) -> None:
        """Clean up resources used by memory integration."""
        await self.vector_db.cleanup()
        await self.document_store.cleanup()
        await self.embedding_manager.cleanup()


class StorageMemory:
    """Manages persistent storage for long-term memory."""
    
    def __init__(self, storage_dir: Union[str, Path]):
        """Initialize storage memory.
        
        Args:
            storage_dir: Directory for storing memory files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
    def store(
        self,
        memory_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store memory data with metadata.
        
        Args:
            memory_id: Unique identifier for the memory
            data: Memory data to store
            metadata: Optional metadata about the memory
        """
        memory = {
            "data": data,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        file_path = self._get_file_path(memory_id)
        with open(file_path, "w") as f:
            json.dump(memory, f, indent=2)
            
    def retrieve(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored memory data.
        
        Args:
            memory_id: Unique identifier for the memory
            
        Returns:
            Memory data and metadata if found, None otherwise
        """
        file_path = self._get_file_path(memory_id)
        if not file_path.exists():
            return None
            
        with open(file_path) as f:
            return json.load(f)
            
    def update(
        self,
        memory_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update existing memory data.
        
        Args:
            memory_id: Unique identifier for the memory
            data: New memory data
            metadata: Optional new metadata
            
        Returns:
            True if memory was updated, False if not found
        """
        current = self.retrieve(memory_id)
        if current is None:
            return False
            
        current["data"].update(data)
        if metadata:
            current["metadata"].update(metadata)
        current["timestamp"] = datetime.utcnow().isoformat()
        
        file_path = self._get_file_path(memory_id)
        with open(file_path, "w") as f:
            json.dump(current, f, indent=2)
            
        return True
        
    def delete(self, memory_id: str) -> bool:
        """Delete stored memory data.
        
        Args:
            memory_id: Unique identifier for the memory
            
        Returns:
            True if memory was deleted, False if not found
        """
        file_path = self._get_file_path(memory_id)
        if not file_path.exists():
            return False
            
        os.remove(file_path)
        return True
        
    def list_memories(self) -> List[str]:
        """List all stored memory IDs.
        
        Returns:
            List of memory IDs
        """
        return [
            f.stem
            for f in self.storage_dir.glob("*.json")
            if f.is_file()
        ]
        
    def _get_file_path(self, memory_id: str) -> Path:
        """Get file path for a memory ID.
        
        Args:
            memory_id: Unique identifier for the memory
            
        Returns:
            Path object for the memory file
        """
        return self.storage_dir / f"{memory_id}.json"


class LongTermStorage(BaseMemory):
    """Long-term memory storage implementation."""
    
    def __init__(
        self,
        name: str,
        backend: MemoryBackend,
        namespace: str = "default",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize long-term storage.
        
        Args:
            name: Memory name
            backend: Memory backend
            namespace: Storage namespace (default: default)
            config: Optional memory configuration
        """
        super().__init__(name, backend, config)
        self._namespace = namespace
        self._metadata_key = f"metadata:{namespace}"
        self._messages_key = f"messages:{namespace}"
        
    @property
    def namespace(self) -> str:
        """Return storage namespace."""
        return self._namespace
        
    async def add_message(self, message: Message) -> None:
        """Add message to memory.
        
        Args:
            message: Message to add
            
        Raises:
            MemoryError: If message cannot be stored
        """
        try:
            # Get current messages
            messages = await self.get_messages()
            
            # Add timestamp to metadata
            message.metadata["stored_at"] = datetime.utcnow().isoformat()
            message.metadata["namespace"] = self._namespace
            
            # Add new message
            messages.append(message)
            
            # Store messages
            await self._backend.store(
                self._messages_key,
                [msg.to_dict() for msg in messages],
            )
            
            # Update metadata
            await self._update_metadata(message)
            
        except Exception as e:
            raise MemoryError(f"Failed to add message: {e}") from e
            
    async def get_messages(
        self,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Message]:
        """Get messages from memory.
        
        Args:
            limit: Optional message limit
            filters: Optional message filters
            
        Returns:
            List of messages
            
        Raises:
            MemoryError: If messages cannot be retrieved
        """
        try:
            # Get stored messages
            data = await self._backend.retrieve(self._messages_key)
            if not data:
                return []
                
            # Convert to messages
            messages = [Message.from_dict(msg) for msg in data]
            
            # Apply filters
            if filters:
                messages = [
                    msg for msg in messages
                    if all(
                        msg.metadata.get(k) == v
                        for k, v in filters.items()
                    )
                ]
                
            # Apply limit
            if limit is not None:
                messages = messages[-limit:]
                
            return messages
            
        except Exception as e:
            raise MemoryError(f"Failed to get messages: {e}") from e
            
    async def clear(self) -> None:
        """Clear memory.
        
        Raises:
            MemoryError: If memory cannot be cleared
        """
        try:
            # Delete messages
            await self._backend.delete(self._messages_key)
            
            # Delete metadata
            await self._backend.delete(self._metadata_key)
            
        except Exception as e:
            raise MemoryError(f"Failed to clear memory: {e}") from e
            
    async def get_metadata(self) -> Dict[str, Any]:
        """Get storage metadata.
        
        Returns:
            Storage metadata
            
        Raises:
            MemoryError: If metadata cannot be retrieved
        """
        try:
            data = await self._backend.retrieve(self._metadata_key)
            return data or {}
            
        except Exception as e:
            raise MemoryError(f"Failed to get metadata: {e}") from e
            
    async def _update_metadata(self, message: Message) -> None:
        """Update storage metadata.
        
        Args:
            message: Message to update metadata with
            
        Raises:
            MemoryError: If metadata cannot be updated
        """
        try:
            # Get current metadata
            metadata = await self.get_metadata()
            
            # Update metadata
            metadata.update({
                "last_updated": datetime.utcnow().isoformat(),
                "message_count": metadata.get("message_count", 0) + 1,
                "roles": list(set(metadata.get("roles", []) + [message.role])),
            })
            
            # Store metadata
            await self._backend.store(self._metadata_key, metadata)
            
        except Exception as e:
            raise MemoryError(f"Failed to update metadata: {e}") from e
            
    def validate(self) -> None:
        """Validate memory state."""
        super().validate()
        
        if not self._namespace:
            raise ValueError("Storage namespace cannot be empty")
