# Text Embeddings

PepperPy AI provides powerful text embedding capabilities for semantic text processing.

## Overview

Text embeddings convert text into numerical vectors that capture semantic meaning. These vectors can be used for:
- Semantic search
- Text similarity
- Document clustering
- Content recommendation

## Embedding Providers

### OpenAI Embeddings
- Uses OpenAI's text-embedding models
- High-quality semantic representations
- Fast processing speed

### Sentence Transformers
- Local embedding generation
- Multiple model options
- Customizable for specific domains

## Using Embeddings

### Basic Usage

```python
from pepperpy.client import PepperPyAI
from pepperpy.config import Config

async def embedding_example():
    config = Config()
    client = PepperPyAI(config)
    
    # Get embedding for text
    embedding = await client.get_embedding("Hello, world!")
    print(len(embedding))  # Vector dimension
```

### Batch Processing

```python
async def batch_embedding_example():
    config = Config()
    client = PepperPyAI(config)
    
    texts = [
        "First document",
        "Second document",
        "Third document"
    ]
    
    embeddings = await client.get_embeddings(texts)
    print(len(embeddings))  # Number of documents
```

## Embedding Configuration

Configure embedding settings:

```python
from pepperpy.config import Config

config = Config(
    embedding_provider="openai",
    embedding_model="text-embedding-ada-002",
    embedding_dimension=1536
)
```

## Advanced Features

### Semantic Search

```python
from pepperpy.embeddings import semantic_search

async def search_example():
    config = Config()
    client = PepperPyAI(config)
    
    # Documents to search
    documents = [
        "Python is a programming language",
        "Java is also a programming language",
        "Cats are animals"
    ]
    
    # Query text
    query = "programming languages"
    
    # Search documents
    results = await semantic_search(
        client,
        query,
        documents,
        top_k=2
    )
    
    for doc, score in results:
        print(f"Score: {score:.2f}, Document: {doc}")
```

### Document Clustering

```python
from pepperpy.embeddings import cluster_documents

async def clustering_example():
    config = Config()
    client = PepperPyAI(config)
    
    documents = [
        "Python code example",
        "Java tutorial",
        "Python programming",
        "Cat behavior",
        "Dog training",
        "Java development"
    ]
    
    clusters = await cluster_documents(
        client,
        documents,
        n_clusters=3
    )
    
    for i, cluster in enumerate(clusters):
        print(f"Cluster {i}:", cluster)
```

## Best Practices

1. **Model Selection**
   - Choose appropriate embedding models
   - Consider dimensionality vs. performance
   - Use domain-specific models when needed

2. **Performance**
   - Batch process when possible
   - Cache embeddings for reuse
   - Use appropriate vector dimensions

3. **Quality**
   - Preprocess text appropriately
   - Handle multilingual content
   - Validate embedding quality

4. **Storage**
   - Use efficient vector storage
   - Implement vector indexing
   - Consider dimensionality reduction

## Environment Variables

Configure embedding settings:

```bash
PEPPERPY_EMBEDDING_PROVIDER=openai
PEPPERPY_EMBEDDING_MODEL=text-embedding-ada-002
PEPPERPY_EMBEDDING_DIMENSION=1536
```

## Examples

### Text Similarity

```python
from pepperpy.embeddings import cosine_similarity

async def similarity_example():
    config = Config()
    client = PepperPyAI(config)
    
    text1 = "Python programming"
    text2 = "Python development"
    
    # Get embeddings
    emb1 = await client.get_embedding(text1)
    emb2 = await client.get_embedding(text2)
    
    # Calculate similarity
    similarity = cosine_similarity(emb1, emb2)
    print(f"Similarity: {similarity:.2f}")
```

### Custom Embedding Model

```python
from pepperpy.embeddings import SentenceTransformer

async def custom_model_example():
    config = Config(
        embedding_provider="sentence_transformers",
        embedding_model="all-MiniLM-L6-v2"
    )
    client = PepperPyAI(config)
    
    embedding = await client.get_embedding("Custom model example")
    print(len(embedding))
``` 