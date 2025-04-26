# PepperPy

A Pythonic Framework for AI Agents and LLM Capabilities

## Requirements

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Ultra-fast Python package installer and resolver

## Installation

### Automated Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/pepperpy.git
cd pepperpy

# Run the installation script
./scripts/install.sh
```

The installation script will:
- Check if uv is installed and install it if necessary
- Set up the virtual environment
- Install project dependencies

### Manual Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yourusername/pepperpy.git
cd pepperpy

# Create virtual environment and install dependencies
uv venv
uv sync

# Optional: Install development dependencies
uv add --dev pytest pytest-asyncio mypy ruff black
uv sync
```

## Basic Usage

PepperPy provides a unified CLI for accessing its features:

```bash
# General help
uv run python -m pepperpy --help

# RAG text processing
uv run python -m pepperpy rag --text "Example text" --summary
```

## Development

The project uses helpful development scripts:

```bash
# Activate the virtual environment (optional)
source scripts/activate

# Development helper script
./scripts/dev.sh help     # Show all commands
./scripts/dev.sh test     # Run tests
./scripts/dev.sh lint     # Run linters
./scripts/dev.sh format   # Format code
./scripts/dev.sh clean    # Clean build artifacts
./scripts/dev.sh tree     # Show dependency tree
```

Working with dependencies:

```bash
# Add a new dependency
uv add package_name

# Add a development dependency
uv add --dev package_name

# Remove a dependency
uv remove package_name

# Update lockfile
uv lock

# Sync dependencies
uv sync

# Upgrade dependencies
uv lock --upgrade

# View dependency tree
uv tree
```

## Architecture

PepperPy is organized into vertical domains, each responsible for a specific capability:

- **LLM**: Interaction with language models
- **RAG**: Retrieval Augmented Generation 
- **Embedding**: Text embedding generation
- **Content**: Content processing
- **Agent**: Autonomous agents and assistants
- **Tool**: Tools and integrations
- **Workflow**: Pipeline orchestration

## Project Structure

```
pepperpy/          # Core library implementation
├── agent/         # Agent capabilities and assistants
├── content/       # Content processing and manipulation
├── core/          # Foundational components and utilities
├── embedding/     # Text embedding functionality
├── llm/           # Language model orchestration
├── orchestration/ # Workflow coordination
├── plugin/        # Plugin system implementation
├── rag/           # Retrieval Augmented Generation
├── storage/       # Data persistence
├── tool/          # Tool interfaces and implementations
├── tts/           # Text-to-speech capabilities
├── utils/         # Shared utilities
└── workflow/      # Workflow definitions and execution

plugins/           # Plugin implementations
├── agent/         # Agent plugins
├── embedding/     # Embedding provider plugins
├── llm/           # LLM provider plugins
├── rag/           # RAG implementation plugins
├── storage/       # Storage plugins
├── tool/          # Tool plugins
└── workflow/      # Workflow implementation plugins

api/               # API server implementation
├── routes/        # API route definitions
└── services/      # Service implementations for API

ui/                # Web UI implementation
```

## Development Environment Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Create a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install backend dependencies:

```bash
uv sync
```

3. Set up environment variables (create a `.env` file in the project root):

```
API_PORT=8000
WEB_PORT=3000
```

### Frontend Setup

1. Install frontend dependencies:

```bash
cd ui
npm install
```

## Running the Application

### Running with the Convenience Script

The easiest way to run the application is with the provided script:

```bash
# Make the script executable
chmod +x scripts/run_servers.sh

# Run the application
./scripts/run_servers.sh
```

This will start both the API server and the React frontend. The application will be available at:
- API: http://localhost:8000
- Frontend: http://localhost:3000 (or port 3001 if 3000 is already in use)

To stop the servers:

```bash
./scripts/stop_servers.sh
```

### Running Manually

#### API Server

```bash
cd api
uv run python -m uvicorn main:app --reload --port 8000
```

#### Web Frontend

```bash
cd ui
npm run dev
```

## Architecture

### Core Architecture

PepperPy uses a plugin-based architecture with clear separation between abstract interfaces and concrete implementations. The core modules define the interfaces and the plugins implement them.

### API Architecture

The API server uses FastAPI and follows a service-oriented architecture with dependency injection. Each domain (workflow, governance, etc.) has its own service implementation that encapsulates the business logic.

### UI Architecture

The UI is built with React, TypeScript, and Tailwind CSS. It communicates with the API server to perform operations and retrieve data.

## Features

- Task management with todos
- Workflow execution and management
- API governance assessment
- Agent-to-agent communication simulation

## Contributing

Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 