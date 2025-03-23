# PepperPy

A modular framework for building AI-powered applications.

## Features

- 🤖 **Multi-Agent Collaboration**: Create groups of AI agents that work together to solve complex tasks
- 🔍 **Retrieval Augmented Generation (RAG)**: Enhance AI responses with relevant information from your data
- 🔌 **Modular Design**: Mix and match different LLM providers, vector stores, and agent architectures
- 🛠️ **Easy to Use**: Simple, intuitive APIs for common AI tasks
- 🔄 **Extensible**: Add your own providers and tools with minimal boilerplate

## Installation

```bash
pip install pepperpy
```

## Quick Start

### Using RAG

```python
from pepperpy.rag import SupabaseProvider
from pepperpy.rag.config import SupabaseConfig

# Initialize provider
provider = SupabaseProvider(
    config=SupabaseConfig(
        url="your-supabase-url",
        key="your-supabase-key",
        collection="documents",
    )
)

# Query documents
results = await provider.query("What is machine learning?")
for doc in results:
    print(doc.content)

# Clean up
await provider.shutdown()
```

### Using LLM Providers

```python
from pepperpy.llm import OpenRouterProvider

# Initialize provider
provider = OpenRouterProvider(
    api_key="your-api-key",
    model="anthropic/claude-3-opus-20240229",
)

# Generate text
response = await provider.generate(
    prompt="Explain quantum computing in simple terms.",
    max_tokens=500,
)
print(response.text)

# Clean up
await provider.cleanup()
```

### Combining RAG and Agents

```python
from pepperpy.agents import create_agent_group, execute_task, cleanup_group
from pepperpy.llm import OpenRouterProvider
from pepperpy.rag import SupabaseProvider
from pepperpy.rag.config import SupabaseConfig

# Initialize providers
llm = OpenRouterProvider(
    api_key="your-api-key",
    model="anthropic/claude-3-opus-20240229",
)

rag = SupabaseProvider(
    config=SupabaseConfig(
        url="your-supabase-url",
        key="your-supabase-key",
        collection="documents",
    )
)

# Create agent group
group_id = await create_agent_group(
    agents=[
        {
            "type": "assistant",
            "name": "researcher",
            "system_message": "You are a research assistant.",
        },
        {
            "type": "user",
            "name": "user",
            "system_message": "You are the user requesting information.",
        }
    ],
    name="research_team",
    llm_config=llm.config,
)

try:
    # Query RAG system
    query = "What are the latest AI trends?"
    context = await rag.query(query)

    # Execute task with context
    messages = await execute_task(
        group_id=group_id,
        task=query,
        context={"documents": context},
    )

    # Process messages
    for msg in messages:
        print(f"{msg.role}: {msg.content}")

finally:
    # Clean up
    await cleanup_group(group_id)
    await rag.shutdown()
```

## Documentation

For detailed documentation and examples, visit [docs.pepperpy.com](https://docs.pepperpy.com).

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 