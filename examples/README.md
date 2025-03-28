# PepperPy Examples

This directory contains examples demonstrating various features and use cases of the PepperPy framework.

## Core Examples

- **minimal_example.py**: Basic example showing core framework features and setup
- **smart_pdf_summarizer_example.py**: Complete multi-agent system for PDF analysis

## RAG and Memory Examples

- **memory_rag_example.py**: In-memory RAG implementation
- **sqlite_rag_example.py**: Persistent RAG using SQLite
- **hierarchical_memory_example.py**: Hierarchical memory system
- **document_knowledge_base_example.py**: Document-based knowledge base

## Document Processing Examples

- **document_processing_example.py**: Basic document processing
- **document_workflow_example.py**: Document processing workflow
- **text_processing_workflow_example.py**: Text processing workflow

## Specialized Assistants

- **bi_assistant_example.py**: Business Intelligence assistant
- **repo_analysis_assistant_example.py**: Repository analysis
- **ai_learning_assistant_example.py**: Learning assistant
- **text_refactoring_example.py**: Code refactoring
- **content_generation_example.py**: Content generation
- **podcast_generator_example.py**: Podcast generation

## Running Examples

1. Install required dependencies:
```bash
# Install with all features
pip install "pepperpy[all]"

# Or install specific features
pip install "pepperpy[rag-complete,doc-all]"
```

2. Set up environment variables in `.env`

3. Run specific example:
```bash
python examples/minimal_example.py
```

4. Or run all examples:
```bash
python examples/run_all_examples.py
```

## Directory Structure

```
examples/
├── README.md           # This file
├── .env               # Environment variables
├── run_all_examples.py # Script to run all examples
├── input/             # Input files for examples
├── output/            # Output files from examples
└── data/             # Data files used by examples
```

## Best Practices

When creating new examples:

1. Follow the modular provider pattern
2. Include proper error handling
3. Add clear documentation
4. Use environment variables for configuration
5. Follow PepperPy coding standards 