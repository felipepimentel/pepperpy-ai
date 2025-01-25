# PepperPy

PepperPy is a Python framework for building AI agents with advanced conversation, memory, and knowledge retrieval capabilities.

## Features

### Conversation Management
- Track conversation history with context
- Support for system, user, assistant, and function messages
- Save and load conversations
- Metadata and timestamp tracking

### Memory System
- Short-term and long-term memory management
- Memory importance scoring
- Memory consolidation and retrieval
- Flexible storage backends

### Retrieval Augmented Generation (RAG)
- Document chunking with multiple strategies
- Vector storage for semantic search
- Embedding generation and similarity search
- Context-aware text generation

### LLM Provider Management
- Multiple provider support
- Automatic fallback handling
- Provider statistics tracking
- Streaming response support

## Installation

```bash
pip install pepperpy
```

## Quick Start

### Basic Usage

```python
import asyncio
from pepperpy.llms.llm_manager import LLMManager

async def main():
    # Initialize LLM manager
    llm_manager = LLMManager()
    await llm_manager.initialize({
        "primary": {
            "type": "openrouter",
            "model_name": "anthropic/claude-2",
            "api_key": "your-api-key"
        }
    })
    
    try:
        # Generate text
        response = await llm_manager.generate("Hello, world!")
        print(response.text)
    finally:
        await llm_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### Using Conversation and Memory

```python
from datetime import datetime
from pepperpy.persistence.storage.conversation import Conversation, Message, MessageRole
from pepperpy.providers.memory import MemoryManager

# Create conversation
conversation = Conversation()
conversation.add_message(
    Message(
        role=MessageRole.SYSTEM,
        content="You are a helpful assistant.",
        timestamp=datetime.now()
    )
)

# Create memory manager
memory_manager = MemoryManager()
await memory_manager.add_memory(
    content="User likes Python programming",
    importance=0.8,
    metadata={"type": "preference"}
)

# Query memories
relevant_memories = await memory_manager.query(
    "What does the user like?",
    limit=5
)
```

### Using RAG

```python
from pepperpy.persistence.storage.rag import RAGManager
from pepperpy.persistence.storage.chunking import ChunkManager

# Create RAG manager
rag_manager = RAGManager(
    llm=llm_manager.get_primary_provider(),
    chunk_manager=ChunkManager()
)

# Add documents
await rag_manager.add_document(
    content="Document content...",
    doc_id="doc1",
    metadata={"type": "article"}
)

# Generate with context
response = await rag_manager.generate_with_context(
    query="What is this document about?",
    prompt_template=(
        "Based on the following context, answer the question:\n\n"
        "Context:\n{context}\n\n"
        "Question: {query}\n\n"
        "Answer:"
    )
)
```

## Configuration

### Environment Variables

```bash
# OpenRouter API key
PEPPERPY_API_KEY=your-api-key

# Optional fallback configuration
PEPPERPY_FALLBACK_API_KEY=your-fallback-api-key
PEPPERPY_FALLBACK_MODEL=openai/gpt-4
```

### Provider Configuration

```python
config = {
    "primary": {
        "type": "openrouter",
        "model_name": "anthropic/claude-2",
        "api_key": "your-api-key",
        "temperature": 0.7,
        "max_tokens": 1000
    },
    "fallback": {
        "type": "openrouter",
        "model_name": "openai/gpt-4",
        "api_key": "your-fallback-api-key",
        "temperature": 0.7,
        "max_tokens": 1000,
        "is_fallback": True,
        "priority": 1
    }
}
```

## Examples

Check out the `examples` directory for more detailed examples:

- `agent_with_memory.py`: Demonstrates conversation, memory, and RAG features
- `story_illustrator.py`: Shows how to use LLMs for creative tasks
- More examples coming soon!

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests with `pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file for details
