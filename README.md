# Pepperpy

A flexible and extensible agent system for building intelligent applications.

## Overview

Pepperpy is a Python framework for building intelligent agent-based systems. It provides:

- Flexible agent architecture with standardized communication protocol
- Modular provider system for different AI backends
- Built-in memory management with vector storage
- Event-driven architecture for agent coordination
- Comprehensive logging and monitoring

## Project Structure

The project follows a task-based evolutionary approach:

```plaintext
pepperpy/              # Main package
├── common/            # Common utilities
├── agents/            # Agent system
├── providers/         # Provider implementations
├── memory/           # Memory system
├── events/           # Event system
└── ...

scripts/              # Development tools
├── setup.py          # Environment setup
├── test.py          # Test runner
└── structure/        # Structure management
```

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pepperpy.git
   cd pepperpy
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

3. Run setup script:
   ```bash
   ./scripts/setup.py
   ```

4. Copy environment template:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Development Workflow

1. Check the kanban board in `.product/kanban.md`
2. Pick a task to work on
3. Create a branch: `task/XXX-description`
4. Implement the task
5. Run tests: `./scripts/test.py`
6. Create PR following guidelines

## Project Rules

All development must follow these rules:

1. File Management
   - Follow file header template
   - Use meaningful file names
   - Keep single responsibility

2. Code Quality
   - Follow PEP 8
   - Use type hints
   - Write tests
   - Document public APIs

3. Structure
   - Follow `project_structure.yml`
   - Only create needed components
   - Keep architecture updated

## Testing

Run the test suite:

```bash
# Run all tests
./scripts/test.py

# Run specific tests
./scripts/test.py tests/test_agents

# Skip some checks
./scripts/test.py --no-lint --no-type-check
```

## Contributing

1. Check the kanban board for available tasks
2. Follow the project rules
3. Write tests for new features
4. Update documentation
5. Create a pull request

## License

[Your License Here]
