# RAG Provider Examples

This directory contains examples demonstrating how to use the RAG (Retrieval Augmented Generation) providers in PepperPy.

## Examples

1. **Basic Usage** (`chroma_example.py`)
   - Demonstrates basic vector storage and retrieval
   - Uses in-memory storage
   - Shows simple similarity search and filtering

2. **Persistent Storage** (`chroma_persistent_example.py`)
   - Shows how to use persistent storage
   - Demonstrates more complex metadata filtering
   - Includes multiple search scenarios

3. **Text Embeddings** (`text_embeddings_example.py`)
   - Shows how to use the provider with text embeddings
   - Includes a mock embedding function for demonstration
   - Demonstrates semantic search with text queries

## Running the Examples

1. Make sure you have PepperPy installed:
   ```bash
   pip install -e .
   ```

2. Install additional dependencies:
   ```bash
   pip install numpy chromadb
   ```

3. Run any example:
   ```bash
   python examples/rag/chroma_example.py
   python examples/rag/chroma_persistent_example.py
   python examples/rag/text_embeddings_example.py
   ```

## Notes

- The examples use mock data and embeddings for demonstration purposes
- In a real application, you would use proper embedding models
- The persistent storage example creates a `data/vector_store` directory
- All examples demonstrate async/await usage 