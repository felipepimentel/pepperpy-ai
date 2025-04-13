# PepperPy API Server

## Overview

The PepperPy API Server provides a comprehensive REST API for accessing PepperPy's capabilities. It follows best practices for API design and implements proper abstraction layers to maintain clean architecture.

## Architecture

This API follows PepperPy's core architectural principles:

1. **Service Abstraction** - All access to PepperPy happens through service layers
2. **Dependency Injection** - Services are provided through FastAPI's dependency injection system
3. **Resource Management** - Proper initialization and cleanup of resources

## Components

- **FastAPI Server** - Handles HTTP requests with async/await support
- **Service Layer** - Provides abstraction over PepperPy functionality
- **Routes** - Organizes API endpoints by domain
- **Dependencies** - Manages service instances and dependencies

## Services

The API provides several services:

1. **Workflow Service** - Access to different workflow types (governance, blueprint, etc.)
2. **A2A Service** - Agent-to-agent simulation capabilities
3. **Governance Service** - API governance assessment functionality

## API Endpoints

- `/api/workflows` - List available workflows
- `/api/workflow/{id}/execute` - Execute a workflow
- `/api/workflow/{id}/schema` - Get workflow schema
- `/api/session` - Session management

## Setup and Running

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the API server:
   ```
   uvicorn api.main:app --reload
   ```

3. Access API documentation at `http://localhost:8000/docs`

## Technical Notes

- Built with FastAPI for high performance and async support
- Implements proper dependency injection for service management
- Follows OpenAPI specifications with automatic documentation
- Includes middleware for logging, CORS, and error handling
- Uses Pydantic for data validation

## Integration with PepperPy

This API server integrates with the full PepperPy framework, providing:

1. Real workflow execution
2. Proper resource management
3. Configuration-based provider selection
4. Session management for stateful operations

For a simplified mock implementation suitable for demos, see the `/playground_web` directory. 