# PostgreSQL Storage Backend

The PostgreSQL storage backend provides a scalable and feature-rich implementation of the memory storage system, leveraging PostgreSQL's advanced features for efficient data storage, indexing, and retrieval.

## Features

- Full CRUD operations for memory entries
- Vector similarity search using pgvector
- Full-text search using tsvector
- Automatic index maintenance
- Connection pooling
- Expiration handling
- Comprehensive error handling

## Requirements

### PostgreSQL Setup

1. Install PostgreSQL 14+ with pgvector extension:
   ```bash
   # Using Docker
   docker pull ankane/pgvector:latest
   
   # Or install manually
   sudo apt-get install postgresql-14
   sudo apt-get install postgresql-14-vector
   ```

2. Create database and extensions:
   ```sql
   CREATE DATABASE pepperpy;
   \c pepperpy
   CREATE EXTENSION vector;
   CREATE EXTENSION pg_trgm;
   ```

### Python Dependencies

Add to your requirements.txt:
```
asyncpg>=0.27.0
sentence-transformers>=2.2.0
numpy>=1.24.0
```

## Configuration

```python
from pepperpy.capabilities.memory.storage.config import PostgresConfig
from pepperpy.capabilities.memory.storage.postgres import PostgresStorage

# Configure storage
config = PostgresConfig(
    host="localhost",
    port=5432,
    database="pepperpy",
    user="postgres",
    password="your_password",
    min_size=1,  # Connection pool minimum size
    max_size=10,  # Connection pool maximum size
)

# Create storage instance
storage = PostgresStorage[str, dict](config)

# Initialize storage
await storage.start()
```

## Usage Examples

### Basic Operations

```python
# Store entry
entry = await storage.store(
    key="doc-1",
    value={"content": "Example document"},
    type=MemoryType.SHORT_TERM,
    scope=MemoryScope.SESSION,
    indices={MemoryIndex.SEMANTIC, MemoryIndex.CONTEXTUAL},
)

# Retrieve entry
retrieved = await storage.retrieve("doc-1")

# Delete entry
deleted = await storage.delete("doc-1")
```

### Search Operations

```python
# Semantic search
query = MemoryQuery(
    query="example search query",
    index_type=MemoryIndex.SEMANTIC,
    min_score=0.5,
    limit=10,
)

async for result in storage.search(query):
    print(f"Score: {result.score}, Entry: {result.entry}")

# Find similar entries
async for result in storage.similar("doc-1", limit=5):
    print(f"Score: {result.score}, Entry: {result.entry}")
```

### Index Maintenance

```python
# Reindex semantic embeddings
reindexed = await storage.reindex(MemoryIndex.SEMANTIC)

# Cleanup expired entries
cleaned = await storage.cleanup_expired()
```

## Performance Characteristics

Based on benchmark tests with default configuration:

### Batch Insert Performance
- 100 entries: ~500 ops/sec, ~2ms latency
- 1000 entries: ~400 ops/sec, ~2.5ms latency

### Search Performance
- Semantic search (1000 entries):
  - Average query time: ~50ms
  - ~20 queries/sec
- Full-text search (1000 entries):
  - Average query time: ~10ms
  - ~100 queries/sec

### Reindexing Performance
- Semantic index (1000 entries):
  - ~100 entries/sec
  - ~10ms per entry
- Full-text index (1000 entries):
  - ~500 entries/sec
  - ~2ms per entry

## Resource Requirements

Recommended minimum specifications:
- CPU: 2+ cores
- RAM: 4GB+
- Storage: SSD recommended
- Network: Low latency connection to PostgreSQL

Memory usage scales with:
- Number of active connections
- Size of connection pool
- Size of vector embeddings
- Number of concurrent operations

## Error Handling

The storage backend provides detailed error information through the `MemoryError` class:

```python
try:
    await storage.retrieve("non-existent")
except MemoryError as e:
    print(f"Error type: {e.store_type}")  # "postgres"
    print(f"Error message: {str(e)}")     # Details about the error
```

Common error scenarios:
- Connection failures
- Invalid configuration
- Missing entries
- Index corruption
- Resource exhaustion

## Monitoring

Key metrics to monitor:
- Connection pool utilization
- Query response times
- Index size and growth
- Cache hit rates
- Error rates

## Best Practices

1. Connection Management
   - Use appropriate pool sizes
   - Monitor connection usage
   - Implement retry logic

2. Index Maintenance
   - Schedule regular reindexing
   - Monitor index sizes
   - Clean up expired entries

3. Performance Optimization
   - Use appropriate batch sizes
   - Implement caching if needed
   - Monitor query patterns

4. Error Handling
   - Implement proper error handling
   - Use exponential backoff
   - Log errors appropriately

## Limitations

1. Vector Similarity Search
   - Limited by pgvector capabilities
   - Performance degrades with large vectors
   - Approximate nearest neighbor search

2. Full-text Search
   - English language optimized
   - Limited language support
   - Basic ranking algorithm

3. Scalability
   - Single PostgreSQL instance
   - No built-in sharding
   - Limited by hardware resources 