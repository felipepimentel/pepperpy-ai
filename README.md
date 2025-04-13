# PepperPy

A modern Python framework for AI applications with a focus on vertical domain integration and agent capabilities.

## Project Structure

PepperPy consists of two main components:

1. **API Server** (`/api`) - A FastAPI-based REST API that integrates with the full PepperPy framework
2. **Playground Web UI** (`/playground_web`) - A Flask-based demo application with mock implementations

## Architecture

PepperPy is organized into vertical domains, each with specific responsibilities:

| Domain       | Purpose                              | 
|--------------|--------------------------------------|
| **LLM**      | Interaction with language models     |
| **RAG**      | Retrieval Augmented Generation       |
| **Embedding**| Text embedding generation            | 
| **Content**  | Content processing                   |
| **Agent**    | Autonomous agents and assistants     |
| **Tool**     | Tools and integrations               |
| **Workflow** | Pipeline orchestration               |

## Key Design Principles

1. **Vertical Domain Organization**: Modules are organized by business domain, not technical layer
2. **Provider-Based Abstraction**: Each domain has multiple pluggable providers
3. **Plugin Architecture**: Functionality is extended through a powerful plugin system
4. **Configuration-Driven**: Behavior is controlled through configuration
5. **Resource Management**: Proper initialization and cleanup of resources
6. **Type Safety**: Strong typing throughout the codebase

## API and Workflows

PepperPy includes several workflow capabilities, accessible through both the API Server and Playground:

### API Workflow Types

1. **API Governance** - Assesses API specifications against governance rules
2. **API Blueprint** - Generates API specifications from user stories
3. **API Mock** - Creates mock servers from API specifications
4. **API Evolution** - Analyzes API changes for compatibility
5. **API Ready** - Evaluates APIs for production readiness

## API Server

The API Server (`/api`) provides a comprehensive REST API:

- Built with FastAPI for high performance
- Implements proper dependency injection
- Provides resource management
- Includes session handling

### API Endpoints

- `/api/workflows` - List available workflows
- `/api/workflow/{id}/execute` - Execute a workflow
- `/api/workflow/{id}/schema` - Get workflow schema
- `/api/session` - Session management

## Playground Web UI

The Playground Web UI (`/playground_web`) is a demonstration application:

- Web UI for exploring workflows
- Built with Flask and modern UI components
- Uses mock implementations for quick demos
- Demonstrates the core abstraction pattern

## Getting Started

### Running the API Server

```bash
cd api
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Access the API documentation at `http://localhost:8000/docs`

### Running the Playground

```bash
cd playground_web
pip install -r requirements.txt
python app.py
```

Access the UI at `http://localhost:5000`

## Plugin System

PepperPy uses a robust plugin architecture:

- **Discovery**: Plugins are automatically discovered
- **Configuration**: Plugins define their own configuration schema
- **Lifecycle Management**: Proper initialization and cleanup
- **Extension Points**: Well-defined extension points

## Creating a New Workflow

Workflows are implemented as plugins:

1. Create a directory in `plugins/workflow/`
2. Define a `plugin.yaml` file with metadata and configuration schema
3. Implement a provider class that extends `WorkflowProvider`
4. Add an `__init__.py` with proper exports

Example:
```
plugins/workflow/my_workflow/
├── __init__.py
├── plugin.yaml
└── provider.py
```

## License

MIT

## Contributing

Contributions are welcome! Please follow the coding standards and submit pull requests.