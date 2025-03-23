# PepperPy

A modular Python framework for building AI-powered applications.

## Features

- Retrieval Augmented Generation (RAG)
- Vector storage with multiple backends
- LLM integration with various providers
- AutoGen (collaborative agents)
- Workflow orchestration
- Caching and optimization

## Installation

```bash
pip install pepperpy
```

## Quick Start

### Using RAG

```python
from pepperpy.rag.providers.supabase import SupabaseConfig, SupabaseProvider

# Initialize provider
config = SupabaseConfig(
    url="your-supabase-url",
    key="your-supabase-key",
    collection="documents",
)
provider = SupabaseProvider()
await provider.initialize(config)

# Add documents
await provider.add_documents([
    Document(content="Document 1 content"),
    Document(content="Document 2 content"),
])

# Search documents
results = await provider.search("your query", top_k=3)
```

### Using LLM Provider

```python
from pepperpy.llm.providers.openrouter import OpenRouterProvider

# Initialize provider
provider = OpenRouterProvider(
    api_key="your-api-key",
    model="openai/gpt-4-turbo",
)
await provider.initialize()

# Generate text
response = await provider.generate([
    Message(role="user", content="Hello, how are you?")
])
print(response.content)
```

### Using AutoGen Provider

```python
from pepperpy.agents.providers.autogen import AutoGenConfig, AutoGenProvider
from pepperpy.llm.providers.openrouter import OpenRouterProvider

# Initialize LLM provider
llm_provider = OpenRouterProvider(
    api_key="your-api-key",
    model="openai/gpt-4-turbo",
)
await llm_provider.initialize()

# Configure agents
config = AutoGenConfig(
    name="research-team",
    description="A team of AI agents that help with research tasks",
    agents=[
        {
            "role": "Researcher",
            "goal": "Research and analyze information",
            "llm_config": {
                "model": "openai/gpt-4-turbo",
                "llm_provider": llm_provider,
            },
        }
    ],
)

# Initialize provider
provider = AutoGenProvider()
await provider.initialize(config)

# Execute task
messages = await provider.execute(
    task="Research the latest developments in AI",
    context={"query": "What are the latest AI trends?"},
)
```

### Combining RAG and Agents

```python
from pepperpy.agents.providers.autogen import AutoGenConfig, AutoGenProvider
from pepperpy.llm.providers.openrouter import OpenRouterProvider
from pepperpy.rag.providers.supabase import SupabaseConfig, SupabaseProvider

# Initialize providers
llm_provider = OpenRouterProvider(
    api_key="your-api-key",
    model="openai/gpt-4-turbo",
)
await llm_provider.initialize()

rag_config = SupabaseConfig(
    url="your-supabase-url",
    key="your-supabase-key",
    collection="documents",
)
rag_provider = SupabaseProvider()
await rag_provider.initialize(rag_config)

agent_config = AutoGenConfig(
    name="research-assistant",
    description="Assistant that uses RAG to answer questions",
    agents=[
        {
            "role": "Assistant",
            "goal": "Help users find information using RAG",
            "llm_config": {
                "model": "openai/gpt-4-turbo",
                "llm_provider": llm_provider,
            },
        }
    ],
)
agent_provider = AutoGenProvider()
await agent_provider.initialize(agent_config)

# Execute RAG query
query = "What are the latest AI trends?"
documents = await rag_provider.search(query, top_k=3)

# Use agent to analyze documents
context = {
    "query": query,
    "documents": [doc.content for doc in documents],
}
messages = await agent_provider.execute(
    task="Analyze the documents and answer the query",
    context=context,
)
```

## Documentation

For detailed documentation, visit [docs.pepperpy.ai](https://docs.pepperpy.ai).

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 