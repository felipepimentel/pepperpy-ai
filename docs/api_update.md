# PepperPy API Update: Convergence and Enhancement

## Overview

The PepperPy framework has undergone a significant enhancement to streamline its API while maintaining robustness, extensibility, and flexibility. This document explains the convergence of features into the main `pepperpy.py` file and the elimination of the simplified API approach in favor of a more comprehensive and integrated solution.

## Key Changes

### 1. Consolidation of API in `pepperpy.py`

- Removed `simple_api.py` in favor of integrating all functionality directly into the main `PepperPy` class
- Enhanced the main `PepperPy` class with high-level, intent-based methods for a more intuitive developer experience
- Maintained builder patterns for specialized workflows while adding streamlined methods for common tasks

### 2. New Core API Methods

The main `PepperPy` class now provides these key methods:

- **`ask_query(query, **context)`**: Process any query, automatically detecting intent and routing to appropriate plugins
- **`process_content(content, instruction, **options)`**: Process any content type with flexible instructions
- **`create_content(description, format, **options)`**: Generate any content type based on descriptions
- **`analyze_data(data, instruction, **options)`**: Analyze data with intelligent routing to appropriate analyzers

### 3. Convenience Aliases in Root Module

For even simpler usage, the root module exposes these convenience functions that use the singleton pattern:

```python
from pepperpy import ask, process, create, analyze

# Simple usage examples
response = await ask("What is generative AI?")
summary = await process("document.pdf", "Extract key points")
image = await create("A cat programming in Python", format="image")
insights = await analyze(df, "Identify trends and outliers")
```

### 4. Integration with Orchestrator System

The API now leverages an intelligent orchestration system that:

- Automatically detects content and data types
- Analyzes user intent to route requests
- Selects appropriate plugins based on capabilities and compatibility
- Manages plugin dependencies and lifecycle
- Caches instances for better performance

## Architecture Benefits

This update:

1. **Reduces API Fragmentation**: All core functionality is accessible through a single, consistent interface
2. **Maintains Flexibility**: The builder pattern is still available for advanced use cases
3. **Improves Developer Experience**: Simple tasks require minimal code while complex tasks remain possible
4. **Enhances Discoverability**: Related functionality is grouped logically
5. **Preserves Extensibility**: The plugin system remains as the foundation, with the API acting as a facade

## Migration Guide

### From Simple API

If you were using the `simple_api.py` module:

```python
# Old approach
from pepperpy.core.simple_api import ask, process, create, analyze

# New approach
from pepperpy import ask, process, create, analyze
```

Function signatures and behavior remain the same, so no other changes are needed.

### From Builder Pattern

The builder pattern is still available and recommended for complex workflows:

```python
# Builder pattern for advanced use cases
result = await pepperpy.chat.with_system("You are a historian").with_user("Tell me about Ancient Rome").generate()

# Simple API for common cases
response = await ask("Tell me about Ancient Rome")
```

## Example Usage

```python
import asyncio
from pepperpy import ask, process, create, analyze, PepperPy

# Using convenience functions
async def simple_example():
    # Question answering
    answer = await ask("What are the key features of Python?")
    print(answer)
    
    # Document processing
    summary = await process("report.pdf", "Summarize the key findings")
    print(summary)
    
    # Content creation
    article = await create("A blog post about AI ethics", format="text")
    print(article)
    
    # Data analysis
    import pandas as pd
    df = pd.read_csv("data.csv")
    insights = await analyze(df, "Find patterns and outliers")
    print(insights)

# Using instance with custom configuration
async def advanced_example():
    # Create custom instance with specific plugins
    pp = PepperPy()
    pp.with_llm("openai", api_key="your-key")
    pp.with_rag("chroma")
    
    # Use custom instance methods
    async with pp:
        result = await pp.ask_query("How does transformers architecture work?")
        print(result)
        
        # Use builders for more control
        markdown = await pp.text.with_prompt("Explain transformers").as_markdown().generate()
        print(markdown)

if __name__ == "__main__":
    asyncio.run(simple_example())
    asyncio.run(advanced_example())
```

## Testing

A comprehensive test suite has been added for the new API:

- **Unit Tests**: Tests for the `ExecutionContext` class, `Orchestrator` class, and PepperPy integration.
- **Mock-based Tests**: Tests using mocked components to ensure the API works as expected without requiring actual providers.
- **Convenience Method Tests**: Tests for the top-level convenience methods (`ask`, `process`, `create`, `analyze`).

To run the tests:

```bash
# Run all tests
pytest tests/agents/test_orchestrator.py -v

# Run specific test
pytest tests/agents/test_orchestrator.py::test_convenience_methods -v
```

## Example Code

A complete example of the new API is available in `examples/api_example.py`, which demonstrates:

1. **Simple API Usage**: Using the top-level convenience methods for quick tasks
2. **Advanced API Usage**: Creating a custom PepperPy instance with specific configuration
3. **Builder Pattern Usage**: Using the builder pattern for more control

You can run this example to see the API in action:

```bash
# Run the example
python examples/api_example.py
```

## Automatic Content Type Detection

The API includes an intelligent content type detection system (`pepperpy/discovery/content_type.py`) that can:

- Detect file types based on extension and MIME type
- Detect data types for Python objects (dictionaries, lists, pandas DataFrames, etc.)
- Detect text formats (JSON, HTML, Markdown, code, etc.)

This allows the API to automatically route requests to the appropriate plugins without requiring explicit type information.

## New Features

### 1. Results Caching

The API now includes a sophisticated caching system that improves performance by storing and reusing operation results:

```python
from pepperpy.cache import cached, get_cache

# Use the decorator for automatic function caching
@cached(ttl=3600, namespace="my_operation")
async def expensive_operation(param1, param2):
    # Expensive computation here
    return result

# Or use the cache manually
cache = get_cache(namespace="query_results")
cache_key = cache.generate_key(params, "my_operation")

# Try to get from cache first
result = cache.get(cache_key)
if result is None:
    # Not in cache, perform operation
    result = await perform_expensive_operation(params)
    # Store in cache for future use
    cache.set(cache_key, result, ttl=3600)
```

The caching system features:
- Multiple storage backends (memory, disk)
- Configurable TTL (time-to-live)
- Namespace segmentation
- Fast key generation with xxHash
- Comprehensive statistics
- Decorator for automatic function caching

### 2. Enhanced Intent Analysis

The intent analysis system has been significantly improved to better understand user queries:

```python
from pepperpy.agents.intent import analyze_intent, create_intent_from_query

# Get detailed intent information
intent_type, parameters, confidence = analyze_intent("Compare the sales figures for Q1 and Q2")
# Returns: ("compare", {"items_1": "sales figures for Q1", "items_2": "Q2"}, 0.92)

# Or create a complete intent object
intent = create_intent_from_query("Summarize this article in 5 paragraphs")
print(intent.name)  # "summarize"
print(intent.parameters)  # {"length": "5", "format": "paragraphs"}
print(intent.confidence)  # 0.89
print(intent.get_category())  # IntentCategory.PROCESSING
```

The enhanced system provides:
- Parameter extraction from queries
- Confidence scoring
- Intent categorization
- Semantic matching
- Extended metadata
- Caching for performance

## Next Steps

Future enhancements could include:

1. **Plugin Discovery UI**: A web-based interface for discovering and managing plugins
2. **More Built-in Providers**: Additional default providers for common use cases
3. **Cross-Plugin Communication**: Allow plugins to communicate with each other for complex workflows
4. **Multi-agent Orchestration**: Support for complex workflows involving multiple agents

## Conclusion

The updated API design maintains PepperPy's vision of being both approachable for newcomers and powerful for advanced users. By consolidating functionality in the main `pepperpy.py` file and providing convenient aliases, we've made the framework more cohesive while preserving all the flexibility of the plugin-based architecture. 