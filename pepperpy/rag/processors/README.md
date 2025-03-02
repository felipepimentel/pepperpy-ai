# RAG Processors

The `pepperpy.rag.processors` module provides specialized processors for RAG (Retrieval Augmented Generation) systems, including preprocessing and optimization components.

## Overview

RAG processors handle the transformation, enhancement, and optimization of content for retrieval-augmented generation systems. They provide a unified interface for working with different aspects of RAG while offering specialized functionality for each component.

## Available Processors

### Preprocessing

The preprocessing components handle document preparation and chunking:

```python
from pepperpy.rag.processors import TextChunker, SentenceChunker, ParagraphChunker

# Initialize chunker
chunker = TextChunker(chunk_size=1000, chunk_overlap=200)

# Process document
chunks = await chunker.chunk(document)

# Use sentence-based chunking
sentence_chunker = SentenceChunker(max_sentences=3)
sentence_chunks = await sentence_chunker.chunk(document)
```

Key features:
- Document chunking
- Text segmentation
- Content preparation
- Metadata extraction

### Optimization

The optimization components handle vector optimization and pruning:

```python
from pepperpy.rag.processors import DimensionalityReducer, VectorPruner

# Initialize reducer
reducer = DimensionalityReducer(target_dimensions=128)

# Reduce dimensions
reduced_vectors = await reducer.reduce(vectors)

# Prune vectors
pruner = VectorPruner(threshold=0.7)
pruned_results = await pruner.prune(results)
```

Key features:
- Vector compression
- Dimensionality reduction
- Pruning techniques
- Quality filtering

## Augmenters

The `Augmenter` classes provide ways to enhance RAG components:

```python
from pepperpy.rag.processors import QueryAugmenter, ResultAugmenter, ContextAugmenter

# Augment query
query_augmenter = QueryAugmenter()
augmented_query = await query_augmenter.augment(query)

# Augment results
result_augmenter = ResultAugmenter()
enhanced_results = await result_augmenter.augment(results)
```

## Configuration

All processors accept a configuration dictionary that can be used to customize their behavior:

```python
# Configure chunker
chunker = TextChunker(config={
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "include_metadata": True
})

# Configure reducer
reducer = DimensionalityReducer(config={
    "target_dimensions": 128,
    "method": "pca"
})
```

## Best Practices

1. **Choose the Right Chunker**: Select the appropriate chunking strategy based on your content type.

2. **Balance Chunk Size**: Use appropriate chunk sizes to balance context and relevance.

3. **Apply Optimization Selectively**: Only apply optimization when necessary for performance or quality.

4. **Chain Processors**: Combine multiple processors for complex transformations:
   ```python
   # Chunk document, then optimize vectors
   chunks = await chunker.chunk(document)
   embeddings = await embedder.embed(chunks)
   optimized = await reducer.reduce(embeddings)
   ```

5. **Monitor Performance**: Keep track of how processors affect retrieval quality and adjust accordingly.