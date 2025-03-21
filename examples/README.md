# PepperPy Examples

This directory contains comprehensive examples demonstrating the capabilities of the PepperPy framework. The examples are organized into three main categories:

## 1. Scenarios

Complete, production-ready examples that demonstrate real-world use cases combining multiple PepperPy features:

- `document_processing_pipeline.py`: Complete document processing pipeline combining RAG, memory optimization, caching, and monitoring
- `search_engine_implementation.py`: Full-featured search engine with hybrid search, reranking, and streaming
- `data_management_system.py`: Data management system with validation, versioning, and migration
- `api_gateway_service.py`: API gateway service with connection pooling, batching, and security
- `workflow_orchestration.py`: Workflow orchestration system with plugins and monitoring

## 2. Integrations

Examples showing how to integrate PepperPy with various external systems and services:

- `enterprise_search/`: Integration with enterprise search systems
  - Vector stores (Pinecone, Chroma)
  - Full-text search engines
  - Hybrid search implementations
  
- `document_management/`: Integration with document management systems
  - Document storage providers
  - Version control systems
  - Content management systems
  
- `monitoring_stack/`: Integration with monitoring and observability tools
  - Metrics collection and reporting
  - Distributed tracing
  - Log aggregation

## 3. Tutorials

Step-by-step tutorials to learn PepperPy features:

1. `01_getting_started.py`: Basic concepts and setup
2. `02_building_search.py`: Building a search system
3. `03_document_processing.py`: Document processing and RAG
4. `04_optimization.py`: Performance optimization techniques

## Running the Examples

### Prerequisites

1. Install PepperPy with all optional dependencies:
   ```bash
   pip install pepperpy[all]
   ```

2. Set up required environment variables:
   ```bash
   export PEPPERPY_LOG_LEVEL=INFO
   export PEPPERPY_STORAGE_PATH=./data
   ```

### Running Scenarios

Each scenario is a self-contained example that can be run directly:

```bash
# Run the document processing pipeline example
python examples/scenarios/document_processing_pipeline.py

# Run the search engine implementation example
python examples/scenarios/search_engine_implementation.py
```

### Running Integration Examples

Integration examples may require additional setup:

1. Install integration-specific dependencies:
   ```bash
   pip install -r examples/integrations/requirements.txt
   ```

2. Configure integration settings in `config.yaml`

3. Run the example:
   ```bash
   python examples/integrations/enterprise_search/pinecone_example.py
   ```

### Following Tutorials

Tutorials should be followed in order:

```bash
# Start with the basics
python examples/tutorials/01_getting_started.py

# Move on to search functionality
python examples/tutorials/02_building_search.py
```

## Example Structure

Each example follows a consistent structure:

1. Comprehensive docstring explaining:
   - Purpose and features demonstrated
   - Architecture and design decisions
   - Requirements and setup

2. Code organization:
   - Clear separation of concerns
   - Proper error handling
   - Performance considerations
   - Monitoring and metrics

3. Documentation:
   - Inline comments explaining complex logic
   - Usage examples
   - Expected output

## Contributing New Examples

When adding new examples:

1. Choose the appropriate category (scenarios/integrations/tutorials)
2. Follow the established structure and coding style
3. Include comprehensive documentation
4. Add any necessary dependencies to requirements.txt
5. Update this README.md if adding new categories or major examples

## Support

For questions about the examples:

- Check the [documentation](https://pepperpy.readthedocs.io)
- Open an issue on GitHub
- Join our community Discord server 