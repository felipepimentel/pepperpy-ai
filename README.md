# PepperPy

A framework for building AI-powered applications with RAG (Retrieval Augmented Generation) and LLM capabilities.

## Features

- 🔍 **RAG**: Semantic search and document retrieval
- 🤖 **LLM**: Text generation and chat capabilities
- 💾 **Storage**: File and document management
- 🔄 **Composition**: Combine RAG and LLM operations
- 🎯 **Tools**: Domain-specific utilities (e.g., PDI assistant)

## Installation

```bash
pip install pepperpy
```

## Quick Start

### RAG Operations

```python
import asyncio
from pepperpy import store_and_search, Document

async def main():
    # Store and search documents in one operation
    docs = [
        Document(text="Python is a programming language"),
        Document(text="Python is great for AI development")
    ]
    
    results = await store_and_search(
        documents=docs,
        query="programming language",
        provider_type="annoy"
    )
    
    for doc in results:
        print(doc.text)

asyncio.run(main())
```

### LLM Operations

```python
from pepperpy import generate, chat

# Generate text
response = await generate(
    prompt="Explain what is RAG",
    model="gpt-3.5-turbo"
)

# Chat with history
messages = [
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language."},
    {"role": "user", "content": "What can I build with it?"}
]

response = await chat(messages)
```

### Storage Operations

```python
from pepperpy import save_json, load_json, store_as_document

# Save and load JSON
data = {"name": "John", "age": 30}
await save_json("user.json", data)
loaded = await load_json("user.json")

# Store as searchable document
await store_as_document(
    "user.json",
    data,
    collection_name="users"
)
```

### Composition

```python
from pepperpy import retrieve_and_generate, chat_with_context

# RAG + LLM
response = await retrieve_and_generate(
    query="How to use Python for AI?",
    prompt_template="Based on this context: {context}\n\nAnswer: {query}"
)

# Chat with document context
response = await chat_with_context(
    query="Explain the code",
    history=[{"role": "user", "content": "What is this code about?"}]
)
```

### PDI Assistant Example

```python
from pepperpy import create_and_search_pdi

# Create and search PDIs in one operation
pdis = await create_and_search_pdi(
    user_id="user123",
    goals=[
        "Learn Python programming",
        "Build an AI application"
    ],
    search_query="programming goals",
    output_dir="pdis"
)

for pdi in pdis:
    print(f"User: {pdi['user_id']}")
    print("Goals:", pdi["goals"])
```

## Advanced Usage

### Custom Provider

```python
from pepperpy import PepperPy

async with PepperPy.create().with_rag(
    provider_type="custom",
    provider_class="my_module.CustomProvider",
    **provider_options
) as pepperpy:
    await pepperpy.rag.add(documents)
    results = await pepperpy.rag.search(query_text="search query")
```

### Multiple Components

```python
from pepperpy import PepperPy

async with PepperPy.create().with_rag(
    provider_type="annoy",
    collection_name="docs"
).with_llm(
    provider_type="openai",
    model="gpt-4"
) as pepperpy:
    # Use both RAG and LLM
    docs = await pepperpy.rag.search(query_text="search")
    response = await pepperpy.llm.generate(prompt="generate")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 