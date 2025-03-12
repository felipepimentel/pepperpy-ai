# PepperPy Examples

This directory contains example scripts demonstrating how to use the PepperPy library after the refactoring implemented in TASK-010. These examples showcase the intended API patterns and usage of the library's core modules.

## Available Examples

- **LLM Providers** (`llm_providers.py`): Demonstrates how to use different LLM providers, including OpenAI, Anthropic, and custom providers.
- **RAG Providers** (`rag_providers.py`): Shows how to use Retrieval Augmented Generation with different providers, including basic RAG, vector stores, and hybrid search.
- **Data Providers** (`data_providers.py`): Illustrates how to use the Data storage functionality with different providers and advanced features.

## Prerequisites

- Python 3.9+
- PepperPy library installed
- API keys for the providers you want to use (see `.env.example`)

## Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your API keys in the `.env` file
   ```bash
   cp .env.example .env
   # Edit .env with your favorite editor
   ```

   Alternatively, you can set environment variables directly:
   ```bash
   export OPENAI_API_KEY=your_openai_api_key
   export ANTHROPIC_API_KEY=your_anthropic_api_key
   # etc.
   ```

## Running the Examples

Each example can be run using Poetry:

```bash
# Run the LLM providers example
poetry run python examples/llm_providers.py

# Run the RAG providers example
poetry run python examples/rag_providers.py

# Run the Data providers example
poetry run python examples/data_providers.py
```

## Utility Functions

The examples use common utility functions from `utils.py`:

- `load_env()`: Loads environment variables from a `.env` file
- `check_api_keys()`: Validates that required API keys are available
- `setup_logging()`: Configures logging for the examples

## Notes

- These examples demonstrate the intended API patterns after refactoring.
- Some functionality may not be fully implemented yet.
- The examples are designed to show the API design, not necessarily working code.
- Each example includes detailed comments explaining the functionality being demonstrated.

## Example Output

When running the examples, you'll see output similar to:

```
PepperPy LLM Providers Usage Examples
====================================
This example demonstrates the intended usage patterns after refactoring.
Some functionality may not be fully implemented yet.
This is a demonstration of the API design, not necessarily working code.

Checking required API keys:
✅ OPENAI_API_KEY: Available (required for OpenAI example)
✅ ANTHROPIC_API_KEY: Available (required for Anthropic example)

=== OpenAI Example ===

Creating OpenAI LLM instance...
Generating text with prompt: 'Write a short poem about artificial intelligence.'

Generated text:
[Generated text will appear here]

...
```

## Troubleshooting

If you encounter issues:

1. Ensure all required API keys are set in your environment or `.env` file
2. Check that you're using Python 3.9 or higher
3. Make sure PepperPy is installed correctly
4. Look for error messages in the console output or logs

For more detailed information, refer to the PepperPy documentation. 