# Getting Started

## Installation

```bash
pip install pepperpy
```

## Quick Start

### Basic Chat Agent

```python
from pepperpy.agents import AgentService

# Create service
service = AgentService("my_service")

# Configure chat agent
config = {
    "name": "chat_agent",
    "description": "Basic chat agent",
    "llm_provider": {
        "type": "openrouter",
        "parameters": {
            "model": "gpt-3.5-turbo",
            "api_key": "your_api_key"
        }
    }
}

# Create and use agent
async def main():
    agent = await service.create_agent("chat", config)
    response = await service.process("chat_agent", "Hello!")
    print(response)
    await service.cleanup()
```

### RAG-Enabled Agent

```python
# Configure RAG agent
config = {
    "name": "rag_agent",
    "description": "Document-aware agent",
    "llm_provider": {
        "type": "openrouter",
        "parameters": {
            "model": "gpt-3.5-turbo",
            "api_key": "your_api_key"
        }
    },
    "vector_store_provider": {
        "type": "faiss",
        "parameters": {
            "dimension": 768
        }
    },
    "embedding_provider": {
        "type": "sentence_transformers",
        "parameters": {
            "model": "all-MiniLM-L6-v2"
        }
    }
}

# Create and use agent
async def main():
    agent = await service.create_agent("rag", config)
    
    # Add documents
    documents = [
        "Document 1 content",
        "Document 2 content"
    ]
    await service.process("rag_agent", "add_documents", documents=documents)
    
    # Query documents
    response = await service.process(
        "rag_agent",
        "What do the documents say?",
        use_context=True
    )
    print(response)
    
    await service.cleanup()
```

## Configuration

### Provider Types

1. **LLM Providers**
   - `openrouter`: OpenRouter API
   - `huggingface`: HuggingFace models

2. **Vector Store Providers**
   - `faiss`: FAISS vector store
   - `qdrant`: Qdrant vector database

3. **Embedding Providers**
   - `sentence_transformers`: Local embeddings
   - `openai`: OpenAI embeddings

### Agent Types

1. **Chat Agent**
   - Basic conversation
   - Memory management
   - Required: LLM provider

2. **RAG Agent**
   - Document retrieval
   - Context augmentation
   - Required: LLM, vector store, embedding providers

## Error Handling

```python
from pepperpy.core.errors import PepperpyError

try:
    agent = await service.create_agent("chat", config)
    response = await service.process("chat_agent", "Hello!")
except PepperpyError as e:
    print(f"Error: {str(e)}")
finally:
    await service.cleanup()
```

## Next Steps

1. Read the [Core Concepts](core_concepts.md) guide
2. Check out the [Technical Documentation](technical.md)
3. Explore [Example Projects](examples/) 