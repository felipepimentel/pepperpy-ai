# PepperPy Examples

This directory contains example scripts demonstrating various features and use cases of the PepperPy framework.

## Running Examples

All examples can be run directly using Python:

```bash
# Run from project root
python examples/minimal_example.py
```

## Environment Configuration

All examples use environment variables for configuration. Create a `.env` file in the project root with your credentials:

```
# LLM Configuration
PEPPERPY_LLM__PROVIDER=openai
PEPPERPY_LLM__OPENAI__API_KEY=your-api-key

# RAG Configuration
PEPPERPY_RAG__PROVIDER=chroma
PEPPERPY_EMBEDDINGS__PROVIDER=openai

# TTS Configuration (for examples that use text-to-speech)
PEPPERPY_TTS__PROVIDER=azure
PEPPERPY_TTS__AZURE__API_KEY=your-azure-key
PEPPERPY_TTS__AZURE__REGION=your-azure-region
```

## Available Examples

### Basic Usage

- **[minimal_example.py](minimal_example.py)**: Minimal example of PepperPy usage with a mock LLM provider
- **[complete_example.py](complete_example.py)**: Complete example showing RAG, LLM, and various features

### Domain-Specific Examples

- **[ai_learning_assistant_example.py](ai_learning_assistant_example.py)**: AI-powered learning assistant
- **[bi_assistant_example.py](bi_assistant_example.py)**: Business intelligence assistant
- **[pdi_assistant_example.py](pdi_assistant_example.py)**: PDI assistance

### Content Generation

- **[content_generation_example.py](content_generation_example.py)**: Generate articles and blog posts
- **[podcast_generator_example.py](podcast_generator_example.py)**: Generate podcast content with TTS
- **[text_refactoring_example.py](text_refactoring_example.py)**: Refactor and improve text content

### Data Processing

- **[document_processing_example.py](document_processing_example.py)**: Process documents with workflows
- **[text_chunking_example.py](text_chunking_example.py)**: Text processing and chunking with RAG
- **[text_processing_workflow_example.py](text_processing_workflow_example.py)**: Advanced text processing

### Knowledge Applications

- **[repo_analysis_assistant_example.py](repo_analysis_assistant_example.py)**: Analyze repositories

## Best Practices

When creating or modifying examples, follow these guidelines:

1. **Environment Variables**: Use environment variables exclusively for configuration
2. **Fluent API**: Use PepperPy's fluent API for initialization
3. **Context Managers**: Use async context managers for resource management
4. **I/O Handling**: Let PepperPy manage its I/O resources
5. **Minimal Dependencies**: Avoid unnecessary external dependencies
6. **Good Documentation**: Include clear docstrings and comments

Example of proper initialization:

```python
# Initialize with fluent API - configuration from environment variables
pepper = pepperpy.PepperPy().with_llm().with_rag()

# Use async context manager
async with pepper:
    # Your code here
    await pepper.learn("Knowledge to learn")
    result = await pepper.ask("Question to ask")
```

## Contributing New Examples

When creating new examples:

1. Follow the naming convention: `descriptive_name_example.py`
2. Include a clear module docstring explaining the purpose and features
3. Make the example self-contained and runnable
4. Include comments about required environment variables
5. Follow the standard layout seen in existing examples 