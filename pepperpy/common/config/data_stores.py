"""Configuration for data stores."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from .base import BaseConfig, ConfigError
from .validation import ValidationMixin


@dataclass
class VectorStoreConfig(ValidationMixin):
    """Configuration for vector store."""
    
    type: Literal["faiss", "milvus"] = "faiss"
    dimension: int = 1536
    metric: Literal["cosine", "l2", "ip"] = "cosine"
    index_path: Optional[Path] = None
    
    def validate(self) -> None:
        """Validate vector store configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_string(
            "type",
            self.type,
            choices=("faiss", "milvus")
        )
        self.validate_positive("dimension", self.dimension)
        self.validate_string(
            "metric",
            self.metric,
            choices=("cosine", "l2", "ip")
        )
        if self.type == "faiss" and not self.index_path:
            raise ConfigError("Index path required for FAISS")


@dataclass
class DocumentStoreConfig(ValidationMixin):
    """Configuration for document store."""
    
    type: Literal["file", "s3"] = "file"
    storage_path: Optional[Path] = None
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    def validate(self) -> None:
        """Validate document store configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_string(
            "type",
            self.type,
            choices=("file", "s3")
        )
        self.validate_positive("chunk_size", self.chunk_size)
        self.validate_positive("chunk_overlap", self.chunk_overlap, allow_zero=True)
        
        if self.chunk_overlap >= self.chunk_size:
            raise ConfigError("Chunk overlap must be less than chunk size")
            
        if self.type == "file" and not self.storage_path:
            raise ConfigError("Storage path required for file store")


@dataclass
class MemoryStoreConfig(ValidationMixin):
    """Configuration for memory store."""
    
    type: Literal["hybrid", "redis", "file"] = "hybrid"
    short_term_max_size: int = 1000
    short_term_ttl_seconds: int = 3600
    long_term_storage_path: Optional[Path] = None
    long_term_max_size: int = 10000
    
    def validate(self) -> None:
        """Validate memory store configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_string(
            "type",
            self.type,
            choices=("hybrid", "redis", "file")
        )
        self.validate_positive("short_term_max_size", self.short_term_max_size)
        self.validate_positive("short_term_ttl_seconds", self.short_term_ttl_seconds)
        self.validate_positive("long_term_max_size", self.long_term_max_size)
        
        if self.type in ["hybrid", "file"] and not self.long_term_storage_path:
            raise ConfigError("Long-term storage path required for hybrid/file store")


@dataclass
class DataStoresConfig(BaseConfig, ValidationMixin):
    """Configuration for all data stores."""
    
    vector_store: VectorStoreConfig = VectorStoreConfig()
    document_store: DocumentStoreConfig = DocumentStoreConfig()
    memory_store: MemoryStoreConfig = MemoryStoreConfig()
    
    def validate(self) -> None:
        """Validate all data store configurations.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.vector_store.validate()
        self.document_store.validate()
        self.memory_store.validate() 