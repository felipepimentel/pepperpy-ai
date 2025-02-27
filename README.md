# PepperPy

PepperPy is a Python library that provides a comprehensive set of tools for building and deploying AI-powered applications. It includes modules for Retrieval-Augmented Generation (RAG), observability, security, and analysis.

## Features

- **RAG Module**: Implements retrieval-augmented generation with:
  - Text chunking and preprocessing
  - Document embedding using transformer models
  - Vector and text-based indexing
  - Hybrid retrieval strategies

- **Observability**: Provides tools for:
  - Health checks and monitoring
  - Metrics collection and reporting
  - Performance analysis

- **Security**: Includes features for:
  - Code and content auditing
  - Security event analysis
  - Vulnerability reporting

- **Analysis**: Offers functionality for:
  - Data processing and transformation
  - Metrics collection and analysis
  - Performance optimization

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pepperpy.git
cd pepperpy
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Here's a simple example of using PepperPy's RAG module:

```python
from pepperpy.rag.embedding import TextEmbedder
from pepperpy.rag.indexing import VectorIndexer
from pepperpy.rag.retrieval import VectorRetriever

# Initialize components
embedder = TextEmbedder()
indexer = VectorIndexer()
retriever = VectorRetriever(embedder=embedder, indexer=indexer)

# Initialize the retriever
await retriever.initialize()

# Index some documents
documents = ["First document", "Second document", "Third document"]
embeddings = await embedder.embed(documents)
await indexer.index(embeddings, metadata=[{"id": i} for i in range(len(documents))])

# Retrieve similar documents
results = await retriever.retrieve("query text", k=2)
print(results)

# Clean up
await retriever.cleanup()
```

## Development

1. Install development dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest tests/
```

3. Run linters and formatters:
```bash
black .
isort .
mypy .
pylint pepperpy/
flake8 pepperpy/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
