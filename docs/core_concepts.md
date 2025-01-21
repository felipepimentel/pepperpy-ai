# Core Concepts

## Overview
Pepperpy is a modular and extensible framework for building AI systems. It provides a flexible architecture based on providers and agents, allowing for easy integration of different AI capabilities.

## Key Components

### Providers
Providers are the building blocks of Pepperpy, offering standardized interfaces for different functionalities:

1. **LLM Providers**
   - Handle interactions with language models
   - Support both API-based and local models
   - Manage streaming and batched responses
   - Example: OpenRouter, HuggingFace

2. **Vector Store Providers**
   - Manage vector storage and retrieval
   - Support similarity search operations
   - Handle metadata and filtering
   - Example: FAISS, Qdrant

3. **Embedding Providers**
   - Generate text embeddings
   - Support batched operations
   - Handle different embedding models
   - Example: SentenceTransformers, OpenAI

4. **Memory Providers**
   - Manage conversation history
   - Support message filtering and search
   - Handle state persistence
   - Example: SQLite, Redis

### Agents
Agents are the high-level components that combine providers to create AI applications:

1. **Chat Agent**
   - Basic conversation capabilities
   - Memory management
   - Message handling

2. **RAG Agent**
   - Document retrieval
   - Context augmentation
   - Knowledge base integration

## Architecture

### Provider System
The provider system follows these principles:

1. **Registration**
   - Providers register with a central registry
   - Dynamic provider discovery
   - Type-safe provider access

2. **Configuration**
   - Standardized configuration structure
   - Provider-specific parameters
   - Metadata support

3. **Lifecycle**
   - Initialization and cleanup
   - Resource management
   - Error handling

### Agent Service
The agent service manages agent lifecycle:

1. **Creation**
   - Factory-based agent creation
   - Configuration validation
   - Provider initialization

2. **Management**
   - Agent registration
   - State tracking
   - Resource cleanup

## Best Practices

### Development
1. **Type Safety**
   - Use type hints consistently
   - Validate input/output types
   - Handle type conversions

2. **Error Handling**
   - Use specific error types
   - Include context in errors
   - Clean up on failure

3. **Resource Management**
   - Initialize resources properly
   - Clean up after use
   - Handle cleanup failures

### Configuration
1. **Provider Config**
   ```python
   provider_config = {
       "type": "provider_type",
       "parameters": {
           "key1": "value1",
           "key2": "value2"
       },
       "metadata": {
           "meta1": "value1"
       }
   }
   ```

2. **Agent Config**
   ```python
   agent_config = {
       "name": "agent_name",
       "description": "agent_description",
       "llm_provider": provider_config,
       "vector_store_provider": provider_config,  # Optional
       "embedding_provider": provider_config,     # Optional
       "memory_provider": provider_config,        # Optional
       "parameters": {},
       "metadata": {}
   }
   ```

## Usage Patterns

### Basic Usage
```python
# Create service
service = AgentService("my_service")

# Configure agent
config = {
    "name": "my_agent",
    "description": "Example agent",
    "llm_provider": {
        "type": "openrouter",
        "parameters": {"model": "gpt-3.5-turbo"}
    }
}

# Create and use agent
agent = await service.create_agent("chat", config)
result = await service.process("my_agent", "Hello!")
await service.cleanup()
```

### Advanced Usage
```python
# Configure RAG agent
config = {
    "name": "rag_agent",
    "description": "RAG-enabled agent",
    "llm_provider": {
        "type": "openrouter",
        "parameters": {"model": "gpt-3.5-turbo"}
    },
    "vector_store_provider": {
        "type": "faiss",
        "parameters": {"dimension": 768}
    },
    "embedding_provider": {
        "type": "sentence_transformers",
        "parameters": {"model": "all-MiniLM-L6-v2"}
    }
}

# Create and use agent
agent = await service.create_agent("rag", config)
result = await service.process(
    "rag_agent",
    "Query documents",
    documents=["doc1", "doc2"]
)
await service.cleanup() 