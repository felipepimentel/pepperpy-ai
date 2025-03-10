# PepperPy Framework Documentation

Welcome to the PepperPy Framework documentation. This documentation provides comprehensive information about the framework, its components, and how to use them.

## Overview

PepperPy is a modular Python framework designed for building AI-powered applications. It provides a set of tools and abstractions for working with large language models, retrieval-augmented generation, data processing, and more.

## Documentation Structure

The documentation is organized into the following sections:

- **API Reference**: Detailed reference documentation for the framework's API.
- **User Guide**: Guides and tutorials for using the framework.
- **Developer Guide**: Information for developers who want to contribute to the framework.
- **Examples**: Example code and projects that demonstrate how to use the framework.

## Getting Started

To get started with PepperPy, follow these steps:

1. Install the framework:
   ```bash
   pip install pepperpy
   ```

2. Import the framework in your code:
   ```python
   import pepperpy
   ```

3. Use the framework's components:
   ```python
   # Example: Using the LLM module
   from pepperpy.llm import get_provider, generate_text
   
   # Initialize a provider
   provider = get_provider("openai")
   
   # Generate text
   response = generate_text(provider, "Hello, world!")
   print(response)
   ```

## Key Features

- **Modular Design**: The framework is designed to be modular, allowing you to use only the components you need.
- **Extensible**: You can extend the framework with your own components and providers.
- **Type-Safe**: The framework is built with type safety in mind, providing type hints for all public APIs.
- **Async-First**: The framework is designed to be used with async/await, making it suitable for high-performance applications.
- **Comprehensive**: The framework provides a wide range of tools and abstractions for building AI-powered applications.

## Core Modules

- **LLM**: Integration with large language models.
- **RAG**: Retrieval-augmented generation.
- **Data**: Data processing and persistence.
- **Workflows**: Workflow management.
- **Events**: Event-driven architecture.
- **Plugins**: Plugin system for extending the framework.
- **HTTP**: HTTP client and server.
- **Cache**: Caching system.
- **Storage**: Storage system.
- **Memory**: Memory management.
- **Streaming**: Streaming functionality.
- **Config**: Configuration management.
- **CLI**: Command-line interface.
- **Utils**: Utility functions.
- **Types**: Type definitions.
- **Errors**: Error handling.
- **Interfaces**: Interface definitions.
- **Registry**: Component registry.

## Contributing

We welcome contributions to the framework. Please see the [Developer Guide](./dev/README.md) for more information on how to contribute.

## License

PepperPy is licensed under the MIT License. See the [LICENSE](../LICENSE) file for more information. 