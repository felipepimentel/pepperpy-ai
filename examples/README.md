# PepperPy Examples

This directory contains example applications demonstrating various features of the PepperPy framework.

## Running Examples

Examples can be run using Python from the project root directory:

```bash
python -m examples.minimal_example
```

## Available Examples

### Core Examples

- **minimal_example.py** - Basic example demonstrating core functionality
- **simple_storage_example.py** - Simple file-based storage example
- **pepperpy_example.py** - Example using the main PepperPy framework API

### Advanced Examples (May require additional dependencies)

- **chatbot_example.py** - Build a simple chatbot
- **content_processing_workflow_example.py** - Process content with a workflow
- **discovery_example.py** - Discover plugins and providers
- **intelligent_agents_example.py** - Create intelligent agents
- **knowledge_management_example.py** - Build a knowledge management system
- **llm_completion_example.py** - Use LLMs for text completion
- **llm_embedding_example.py** - Generate embeddings with LLMs
- **llm_stream_example.py** - Stream LLM completions
- **multi_provider_example.py** - Use multiple providers simultaneously
- **repo_analysis_assistant_example.py** - Analyze code repositories
- **tts_example.py** - Generate speech with Text-to-Speech
- **sqlite_storage_example.py** - Store data with SQLite

## Architecture Notes

These examples follow the PepperPy architectural principles:

1. **Indirect Plugin Access** - Never access plugins directly, always use the framework's API
2. **Framework Orchestration** - Let the framework handle initialization, configuration and cleanup
3. **Configuration Strategy** - Use configuration to specify providers and options

## Troubleshooting

If you encounter errors running examples:

1. Make sure you have installed all required dependencies 
2. Check that the necessary plugins are available
3. Verify your environment variables are set correctly
4. Run the `minimal_example.py` first to verify your basic setup 