# PepperPy Framework

PepperPy is a modular Python framework for building AI-powered applications, with a focus on clean architecture and domain-driven design.

## Project Structure

The framework is organized into vertical domains, each responsible for a specific business capability:

```
pepperpy/
├── llm/                  # Language Model Domain
│   ├── __init__.py      
│   ├── provider.py      # Core LLM interfaces
│   └── providers/       # LLM implementations
│       ├── openai/      # OpenAI integration
│       ├── local/       # Local models
│       └── rest/        # REST-based providers
│
├── rag/                  # RAG Domain
│   ├── __init__.py
│   ├── provider.py      # Core RAG interfaces
│   └── providers/       # RAG implementations
│       ├── openai/      # OpenAI embeddings
│       ├── local/       # Local retrieval
│       └── rest/        # REST-based providers
│
├── storage/             # Storage Domain
│   ├── __init__.py
│   ├── provider.py      # Core storage interfaces
│   └── providers/       # Storage implementations
│       ├── sql/        # SQL databases
│       ├── nosql/      # NoSQL databases
│       └── object/     # Object storage
│
├── core/               # Core Framework
│   ├── __init__.py
│   ├── capabilities/   # Capability management
│   ├── errors/        # Error definitions
│   └── base/          # Base classes
│
└── common/            # Shared Utilities
    ├── __init__.py
    ├── logging/
    ├── config/
    └── utils/
```

## Domain Organization

Each domain follows these principles:

1. **Vertical Slicing**: Each module represents a cohesive business domain
2. **Module Independence**: Loose coupling between modules
3. **Clean Interfaces**: Public interfaces exposed via `__init__.py`
4. **Implementation Privacy**: Internal details kept private
5. **Pragmatic Structure**: Structure grows based on actual needs

## Core Principles

1. **Domain-Driven Design**
   - Clear domain boundaries
   - Self-contained modules
   - Domain-specific interfaces

2. **Clean Architecture**
   - Separation of concerns
   - Dependency inversion
   - Interface segregation

3. **Modular Design**
   - Pluggable components
   - Extensible providers
   - Clear dependencies

## Usage

Each domain provides a clean public interface through its `__init__.py`:

```python
# LLM Domain
from pepperpy.llm import LLMProvider, Message
provider = LLMProvider(model_name="gpt-4")
result = await provider.generate("Hello!")

# RAG Domain
from pepperpy.rag import RAGProvider, Document
provider = RAGProvider()
result = await provider.retrieve("query", top_k=3)

# Storage Domain
from pepperpy.storage import StorageProvider
provider = StorageProvider[Dict[str, Any]]()
id = await provider.create("collection", {"key": "value"})
```

## Development

1. **Adding Features**
   - Add to appropriate domain
   - Follow domain interfaces
   - Maintain encapsulation

2. **Creating Providers**
   - Implement domain interfaces
   - Add domain-specific capabilities
   - Follow provider patterns

3. **Testing**
   - Unit test domain logic
   - Integration test providers
   - End-to-end test flows

## Cursor Rules System

This project uses Cursor rules to ensure consistency and quality in AI-assisted development. The rules provide guidance on architecture, coding standards, and implementation patterns.

### Initialize Rules System

To initialize the rules system:

```bash
# Make the initialization script executable
chmod +x scripts/initialize-rules.sh

# Run the initialization script
./scripts/initialize-rules.sh
```

This will:
1. Backup any existing rules
2. Set up the new rules structure
3. Create auto-generated rules

### Rule Management Tools

The project includes tools for managing rules:

- **Rules Updater**: `scripts/rules-updater.py` - Scan codebase, validate rules, generate new rules
- **Rules Initialization**: `scripts/initialize-rules.sh` - Initialize the rules system

For more information, see [.cursor/rules/README.md](.cursor/rules/README.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 