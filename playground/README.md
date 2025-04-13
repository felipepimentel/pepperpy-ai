# PepperPy Playground

A web-based interactive demonstration of PepperPy's capabilities.

![PepperPy Playground](static/img/logo.svg)

## Overview

PepperPy Playground is a web application that allows users to explore and interact with various workflows and features provided by the PepperPy library. It provides a user-friendly interface to:

- Experiment with different API workflows
- Execute workflows with custom inputs
- View results in real-time
- Learn about PepperPy's capabilities

## Features

- **Interactive Workflows**: Try out various PepperPy workflows with a user-friendly interface
- **API Mock Server**: Create functional mock API servers from OpenAPI specifications
- **API Blueprint**: Generate API contracts, documentation, and code from user stories
- **API Governance**: Analyze APIs for compliance with governance rules
- **Agent-to-Agent Communication**: Demonstrate agent-to-agent interactions

## Getting Started

### Prerequisites

- Python 3.8+
- Flask
- PepperPy library

### Installation

1. Make sure PepperPy is installed:
   ```
   pip install pepperpy
   ```

2. Install additional requirements:
   ```
   pip install flask
   ```

3. Run the application:
   ```
   cd playground
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Start a new playground session
2. Select a workflow from the sidebar
3. Configure the workflow parameters
4. Execute the workflow and view the results

## Development

The playground is built with:

- **Backend**: Flask
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Syntax Highlighting**: highlight.js
- **Icons**: Bootstrap Icons

## Directory Structure

```
playground/
├── app.py                  # Flask application
├── static/                 # Static assets
│   ├── css/                # CSS stylesheets
│   ├── js/                 # JavaScript files
│   └── img/                # Images and icons
├── templates/              # HTML templates
│   └── index.html          # Main application template
└── README.md               # This file
```

## Example Workflows

### API Mock Server

This workflow allows you to create and manage mock API servers based on OpenAPI specifications:

1. Upload an OpenAPI specification file
2. Configure server options
3. Start a mock server
4. Interact with the generated API
5. Generate client code in various languages

### API Blueprint

Generate complete API contracts from user stories:

1. Enter user stories that describe API functionality
2. Configure output options
3. Generate OpenAPI specifications, documentation, and code

### API Governance

Analyze APIs for compliance with governance rules:

1. Upload an API specification
2. Select governance rules to apply
3. Generate a compliance report
4. View recommendations for improvement

## License

This project is licensed under the MIT License - see the LICENSE file for details. 