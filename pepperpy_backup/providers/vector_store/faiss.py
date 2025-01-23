"""FAISS vector store provider implementation."""

import faiss
import numpy as np
from typing import Dict, Any, List, Optional
import json
import os

from .base import BaseVectorStoreProvider

@BaseVectorStoreProvider.register("faiss")
class FAISSVectorStore(BaseVectorStoreProvider):
    """FAISS vector store provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider.
        
        Args:
            config: Configuration dictionary for the provider.
        """
        super().__init__(config)
        self.index: Optional[faiss.Index] = None
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.next_id = 0
        self.dimension = config.get("dimension", 768)  # Default for many embedding models
        self.index_path = config.get("index_path", "faiss_index.bin")
        self.metadata_path = config.get("metadata_path", "faiss_metadata.json")
        
    async def initialize(self) -> None:
        """Initialize provider resources."""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                    self.next_id = max(int(id) for id in self.metadata.keys()) + 1
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f)
    
    async def add_vectors(
        self, 
        vectors: List[List[float]], 
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add vectors to the store.
        
        Args:
            vectors: List of vectors to add.
            metadata: Optional metadata for each vector.
            
        Returns:
            List of IDs for the added vectors.
            
        Raises:
            ValueError: If the index is not initialized or vectors have wrong dimension.
        """
        if not vectors:
            return []
            
        if self.index is None:
            raise ValueError("Index not initialized")
            
        vectors_np = np.array(vectors).astype('float32')
        if vectors_np.shape[1] != self.dimension:
            raise ValueError(f"Expected vectors of dimension {self.dimension}, got {vectors_np.shape[1]}")
            
        self.index.add(vectors_np)
        
        ids = []
        for i, vector in enumerate(vectors):
            id = str(self.next_id)
            self.next_id += 1
            ids.append(id)
            
            if metadata and i < len(metadata):
                self.metadata[id] = metadata[i]
            else:
                self.metadata[id] = {}
                
        return ids
    
    async def search(
        self, 
        query_vector: List[float], 
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Vector to search for.
            k: Number of results to return.
            filter_metadata: Optional metadata filters.
            
        Returns:
            List of results with their metadata and scores.
            
        Raises:
            ValueError: If the index is not initialized or query vector has wrong dimension.
        """
        if self.index is None:
            raise ValueError("Index not initialized")
            
        query_np = np.array([query_vector]).astype('float32')
        if query_np.shape[1] != self.dimension:
            raise ValueError(f"Expected query vector of dimension {self.dimension}, got {query_np.shape[1]}")
            
        # Get more results than k to account for filtering
        distances, indices = self.index.search(query_np, k * 2 if filter_metadata else k)
        
        results = []
        seen_ids = set()
        
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS padding for not enough results
                continue
                
            id = str(idx)
            if id in seen_ids:
                continue
                
            metadata = self.metadata.get(id, {})
            
            # Apply metadata filter
            if filter_metadata:
                matches = True
                for key, value in filter_metadata.items():
                    if key not in metadata or metadata[key] != value:
                        matches = False
                        break
                if not matches:
                    continue
            
            results.append({
                "id": id,
                "score": float(distance),
                "metadata": metadata
            })
            
            seen_ids.add(id)
            if len(results) >= k:
                break
                
        return results
    
    async def delete(self, ids: List[str]) -> bool:
        """Delete vectors from the store.
        
        Args:
            ids: List of vector IDs to delete.
            
        Returns:
            True if successful, False otherwise.
            
        Raises:
            ValueError: If the index is not initialized.
        """
        if self.index is None:
            raise ValueError("Index not initialized")
            
        # FAISS doesn't support deletion, so we need to rebuild the index
        vectors = []
        metadata_list = []
        current_metadata = self.metadata.copy()
        
        # Remove deleted IDs from metadata
        for id in ids:
            current_metadata.pop(id, None)
        
        # Create new index
        new_index = faiss.IndexFlatL2(self.dimension)
        self.metadata = {}
        self.next_id = 0
        
        # Re-add remaining vectors
        for id, meta in current_metadata.items():
            vectors.append(self.index.reconstruct(int(id)))
            metadata_list.append(meta)
        
        if vectors:
            await self.add_vectors(vectors, metadata_list)
        
        self.index = new_index
        return True
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a vector by its ID.
        
        Args:
            id: Vector ID.
            
        Returns:
            Vector data with metadata if found, None otherwise.
            
        Raises:
            ValueError: If the index is not initialized.
        """
        if self.index is None:
            raise ValueError("Index not initialized")
            
        if id not in self.metadata:
            return None
            
        try:
            vector = self.index.reconstruct(int(id))
            return {
                "id": id,
                "vector": vector.tolist(),
                "metadata": self.metadata[id]
            }
        except RuntimeError:
            return None
    
    async def update_metadata(self, id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a vector.
        
        Args:
            id: Vector ID.
            metadata: New metadata.
            
        Returns:
            True if successful, False otherwise.
        """
        if id not in self.metadata:
            return False
            
        self.metadata[id].update(metadata)
        return True 