# PepperPy Playground Web UI

## Overview

This is a web-based playground application that demonstrates PepperPy's workflow capabilities. It provides a clean, modern UI that allows users to explore different workflow types, input data, and see the results.

## Architecture

The playground follows PepperPy's architectural principles:

1. **Service Abstraction** - The UI talks to service abstractions rather than directly to plugins
2. **Clean API** - All interactions happen through a well-defined REST API
3. **Resource Management** - Proper initialization and cleanup of resources

## Components

- **Flask Web Server** - Handles HTTP requests and serves the web UI
- **Mock Workflow Service** - Provides simulated workflow functionality
- **REST API** - Exposes workflow capabilities through a clean interface
- **React-based UI** - Modern UI for interacting with workflows

## Available Workflows

1. **API Governance** - Assess APIs against governance rules
2. **API Blueprint** - Generate API specifications from user stories
3. **API Mock** - Create mock servers from API specifications
4. **API Evolution** - Analyze API changes for compatibility

## Setup and Running

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python app.py
   ```

3. Access the UI at `http://localhost:5000`

## Technical Notes

- Uses Flask with async/await support
- Implements a mock service layer that simulates PepperPy's functionality
- UI built with Bootstrap and custom components
- Code editor powered by Ace Editor
- Syntax highlighting with highlight.js

## Integration with PepperPy

This playground uses a mock implementation rather than connecting directly to the PepperPy framework. This enables:

1. Faster loading and execution
2. Demonstration of capabilities without dependencies
3. Consistent behavior for demonstration purposes
4. Clear illustration of the architectural pattern

For a complete implementation that connects to the real PepperPy framework, see the FastAPI-based implementation in the `/api` directory. 