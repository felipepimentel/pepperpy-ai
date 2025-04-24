# PepperPy

An agentic AI framework with a focus on composable, modular architecture for building advanced AI applications.

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

pepperpy-ui/       # React UI implementation
```

## Development Environment Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install backend dependencies:

```bash
pip install -e .
pip install -r api/requirements.txt
```

3. Set up environment variables (create a `.env` file in the project root):

```
API_PORT=8000
WEB_PORT=3000
```

### Frontend Setup

1. Install frontend dependencies:

```bash
cd pepperpy-ui
npm install
```

## Running the Application

### Running with the Convenience Script

The easiest way to run the application is with the provided script:

```bash
# Make the script executable
chmod +x run_react_servers.sh

# Run the application
./run_react_servers.sh
```

This will start both the API server and the React frontend. The application will be available at:
- API: http://localhost:8000
- Frontend: http://localhost:3000 (or port 3001 if 3000 is already in use)

To stop the servers:

```bash
./stop_react_servers.sh
```

### Running Manually

#### API Server

```bash
cd api
uvicorn main:app --reload --port 8000
```

#### React Frontend

```bash
cd pepperpy-ui
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