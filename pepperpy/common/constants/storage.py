"""Storage constants for Pepperpy."""

from enum import Enum
from typing import Final

# Storage types
class StorageType(str, Enum):
    """Storage types."""
    
    MEMORY = "memory"
    FILE = "file"
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    REDIS = "redis"
    S3 = "s3"
    MINIO = "minio"

# Vector store types
class VectorStoreType(str, Enum):
    """Vector store types."""
    
    FAISS = "faiss"
    ANNOY = "annoy"
    HNSWLIB = "hnswlib"
    PGVECTOR = "pgvector"
    REDIS = "redis"
    MILVUS = "milvus"
    WEAVIATE = "weaviate"

# Document store types
class DocumentStoreType(str, Enum):
    """Document store types."""
    
    FILE = "file"
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"
    S3 = "s3"
    MINIO = "minio"

# Memory store types
class MemoryStoreType(str, Enum):
    """Memory store types."""
    
    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"
    SQLITE = "sqlite"

# Cache types
class CacheType(str, Enum):
    """Cache types."""
    
    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"
    FILE = "file"

# Default storage settings
DEFAULT_VECTOR_DIMENSION: Final[int] = 1536
DEFAULT_INDEX_PATH: Final[str] = "indexes"
DEFAULT_CACHE_TTL: Final[int] = 3600
DEFAULT_BATCH_SIZE: Final[int] = 1000
DEFAULT_MAX_CONNECTIONS: Final[int] = 10

# Distance metrics
class DistanceMetric(str, Enum):
    """Distance metrics for vector similarity."""
    
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"
    HAMMING = "hamming"

# Index types
class IndexType(str, Enum):
    """Index types."""
    
    FLAT = "flat"
    IVF = "ivf"
    HNSW = "hnsw"
    LSH = "lsh"
    PQ = "pq"

# Storage formats
class StorageFormat(str, Enum):
    """Storage formats."""
    
    JSON = "json"
    YAML = "yaml"
    PICKLE = "pickle"
    PARQUET = "parquet"
    CSV = "csv"
    BINARY = "binary"

# Compression types
class CompressionType(str, Enum):
    """Compression types."""
    
    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bzip2"
    LZ4 = "lz4"
    ZSTD = "zstd" 