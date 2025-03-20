# PepperPy Examples

This directory contains example scripts demonstrating how to use various features of the PepperPy framework.

## Structure

```
examples/
├── basic/              # Basic usage examples
│   └── simple_example.py
├── advanced/           # Advanced features and optimizations
│   ├── advanced_caching_example.py
│   ├── benchmarking_example.py
│   ├── data_compression_example.py
│   ├── memory_optimization_example.py
│   └── parallel_processing_example.py
├── integrations/       # Integration examples
│   ├── integrated_example.py
│   ├── lifecycle_example.py
│   └── monitoring_example.py
└── features/          # Feature-specific examples
    ├── api_versioning_example.py
    ├── batching_example.py
    ├── chainable_api_example.py
    ├── connection_pooling_example.py
    ├── context_managers_example.py
    ├── data_integrity_example.py
    ├── data_validation_pipeline_example.py
    ├── decorator_patterns_example.py
    ├── document_versioning_example.py
    ├── fluent_interface_example.py
    ├── http_utils_example.py
    ├── hybrid_search_example.py
    ├── metrics_example.py
    ├── pagination_example.py
    ├── plugin_system_example.py
    ├── query_planning_example.py
    ├── rag_example.py
    ├── rag_pipeline_example.py
    ├── reranking_example.py
    ├── resource_management_example.py
    ├── schema_migration_example.py
    ├── security_example.py
    ├── simplified_imports_example.py
    ├── storage_example.py
    ├── streaming_example.py
    └── workflow_example.py
```

## Running Examples

1. Install PepperPy:
```bash
pip install pepperpy
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. Run an example:
```bash
# Run a basic example
python examples/basic/simple_example.py

# Run an advanced example
python examples/advanced/benchmarking_example.py

# Run an integration example
python examples/integrations/monitoring_example.py
```

## Example Categories

### Basic Examples
Simple examples demonstrating core functionality:
- Basic usage patterns
- Common use cases
- Getting started guides

### Advanced Examples
Examples showcasing advanced features and optimizations:
- Performance optimization
- Memory management
- Parallel processing
- Caching strategies
- Benchmarking

### Integration Examples
Examples demonstrating system integration:
- Monitoring and logging
- Lifecycle management
- System integration patterns
- End-to-end workflows

### Feature Examples
Examples for specific features and components:
- RAG (Retrieval Augmented Generation)
- Workflow management
- API patterns
- Data validation
- Security features

## Contributing

When adding new examples:
1. Follow the [documentation guidelines](../docs/CONTRIBUTING.md)
2. Include docstrings with clear explanations
3. Add requirements if needed
4. Update this README
5. Place in appropriate category directory 