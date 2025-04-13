#!/usr/bin/env python3
"""
PepperPy Playground Web Application

This web application provides a simple interface to explore and test
PepperPy's workflow capabilities, demonstrating the power of the library
without exposing plugin implementations directly.
"""

import os
import json
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from flask import Flask, render_template, request, jsonify, after_this_request, send_from_directory
from flask_cors import CORS

# Local imports
from mock_api_service import MockWorkflowService

app = Flask(__name__)
CORS(app)

# Create a global workflow service instance
workflow_service = MockWorkflowService()
initialized = False

# Initialize the mock API service
mock_service = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.before_request
async def setup_service():
    """Initialize service before first request."""
    global initialized
    if not initialized:
        await workflow_service.initialize()
        initialized = True

    # Add no-cache headers to all responses
    @after_this_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


@app.teardown_appcontext
async def cleanup_service(exception=None):
    """Clean up service when app context is torn down."""
    global initialized
    if initialized:
        await workflow_service.cleanup()
        initialized = False


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route('/api/workflows', methods=['GET'])
async def get_workflows():
    """Get all available workflows."""
    global mock_service
    if mock_service is None:
        mock_service = MockWorkflowService()
        await mock_service.initialize()
    
    workflows = await mock_service.get_available_workflows()
    return jsonify({"workflows": workflows})


@app.route('/api/components', methods=['GET'])
async def get_workflow_components():
    """Get available workflow components for custom workflow building."""
    global mock_service
    if mock_service is None:
        mock_service = MockWorkflowService()
        await mock_service.initialize()
    
    components = await mock_service.get_workflow_components()
    return jsonify(components)


@app.route('/api/workflows/custom', methods=['POST'])
async def create_custom_workflow():
    """Create a new custom workflow."""
    global mock_service
    if mock_service is None:
        mock_service = MockWorkflowService()
        await mock_service.initialize()
    
    workflow_data = request.json
    try:
        result = await mock_service.create_custom_workflow(workflow_data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating custom workflow: {str(e)}")
        return jsonify({"status": "error", "message": f"Internal error: {str(e)}"}), 500


@app.route('/api/workflows/custom/<workflow_id>', methods=['PUT'])
async def update_custom_workflow(workflow_id):
    """Update an existing custom workflow."""
    global mock_service
    if mock_service is None:
        mock_service = MockWorkflowService()
        await mock_service.initialize()
    
    workflow_data = request.json
    try:
        result = await mock_service.update_custom_workflow(workflow_id, workflow_data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating custom workflow: {str(e)}")
        return jsonify({"status": "error", "message": f"Internal error: {str(e)}"}), 500


@app.route('/api/workflows/custom/<workflow_id>', methods=['DELETE'])
async def delete_custom_workflow(workflow_id):
    """Delete a custom workflow."""
    global mock_service
    if mock_service is None:
        mock_service = MockWorkflowService()
        await mock_service.initialize()
    
    try:
        result = await mock_service.delete_custom_workflow(workflow_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error deleting custom workflow: {str(e)}")
        return jsonify({"status": "error", "message": f"Internal error: {str(e)}"}), 500


@app.route('/api/workflow/<workflow_id>/schema', methods=['GET'])
async def get_workflow_schema(workflow_id):
    """Get schema for a specific workflow."""
    global mock_service
    if mock_service is None:
        mock_service = MockWorkflowService()
        await mock_service.initialize()
    
    try:
        workflow = None
        for wf in await mock_service.get_available_workflows():
            if wf['id'] == workflow_id:
                workflow = wf
                break
                
        if not workflow:
            return jsonify({"status": "error", "message": f"Workflow not found: {workflow_id}"}), 404
            
        # If it's a built-in workflow, get the schema from the service
        if workflow_id in mock_service._workflows:
            schema = mock_service._workflows[workflow_id].get('schema', {})
            return jsonify({
                "id": workflow_id,
                "name": workflow.get('name', 'Unknown'),
                "description": workflow.get('description', ''),
                "schema": schema
            })
        else:
            # For custom workflows
            return jsonify({
                "id": workflow_id,
                "name": workflow.get('name', 'Custom Workflow'),
                "description": workflow.get('description', ''),
                "schema": workflow.get('schema', {})
            })
    except Exception as e:
        logger.error(f"Error getting workflow schema: {str(e)}")
        return jsonify({"status": "error", "message": f"Internal error: {str(e)}"}), 500


@app.route('/api/workflow/<workflow_id>/execute', methods=['POST'])
async def execute_workflow(workflow_id):
    """Execute a workflow."""
    global mock_service
    if mock_service is None:
        mock_service = MockWorkflowService()
        await mock_service.initialize()
    
    try:
        data = request.json or {}
        input_data = data.get('input_data', {})
        config = data.get('config', {})
        
        result = await mock_service.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            config=config
        )
        
        return jsonify(result)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        return jsonify({"status": "error", "message": f"Internal error: {str(e)}"}), 500


@app.route('/api/samples/<workflow_id>', methods=['GET'])
def get_workflow_samples(workflow_id):
    """Get sample inputs for a specific workflow."""
    samples = {
        "api-governance": [
            {
                "name": "Basic Security Check",
                "description": "Check a sample API for security issues",
                "input_data": {
                    "spec_url": "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/petstore.yaml",
                    "governance_rules": ["security", "standards"],
                    "output_format": "json"
                }
            },
            {
                "name": "Comprehensive Check",
                "description": "Check a sample API for all governance issues",
                "input_data": {
                    "spec_url": "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/petstore.yaml",
                    "governance_rules": ["security", "standards", "schema", "documentation"],
                    "output_format": "markdown"
                }
            }
        ],
        "simple-chat": [
            {
                "name": "Basic Question",
                "description": "Ask a simple question to the LLM",
                "input_data": {
                    "message": "What is PepperPy and how does it help with LLM integration?",
                    "model": "gpt-4o-mini",
                    "system_prompt": "You are a helpful assistant explaining PepperPy, a Python framework for LLM integration."
                }
            },
            {
                "name": "Code Example",
                "description": "Ask for a code example",
                "input_data": {
                    "message": "Write a simple Python function that calculates the Fibonacci sequence up to n terms.",
                    "model": "gpt-4o-mini",
                    "system_prompt": "You are a coding assistant. Provide clear, well-documented code examples."
                }
            }
        ],
        "api-blueprint": [
            {
                "name": "User Authentication API",
                "description": "Generate an API for user authentication",
                "input_data": {
                    "user_stories": "Feature: User Authentication\n\nScenario: User Registration\nGiven a new user with email and password\nWhen the user submits registration form\nThen a new account should be created\n\nScenario: User Login\nGiven a registered user\nWhen the user provides correct credentials\nThen the user should be authenticated and receive a token",
                    "api_name": "Authentication API",
                    "api_version": "1.0.0"
                }
            }
        ],
        "api-mock": [
            {
                "name": "Pet Store Mock",
                "description": "Create a mock server for the Pet Store API",
                "input_data": {
                    "spec_url": "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/petstore.yaml",
                    "port": 8080
                }
            }
        ],
        "api-evolution": [
            {
                "name": "Pet Store API Evolution",
                "description": "Check for breaking changes between two versions",
                "input_data": {
                    "old_spec_url": "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/petstore.yaml",
                    "new_spec_url": "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/petstore-expanded.yaml",
                    "check_breaking": True
                }
            }
        ]
    }
    
    # Return samples for the requested workflow
    if workflow_id in samples:
        return jsonify(samples[workflow_id])
    else:
        return jsonify([])  # Return empty array if no samples exist


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


def run_async(coro):
    """Run an async function in a synchronous context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# Wrap async route handlers for Flask
def async_route(route_function):
    """Decorator to handle async routes in Flask."""
    def wrapper(*args, **kwargs):
        return run_async(route_function(*args, **kwargs))
    wrapper.__name__ = route_function.__name__
    return wrapper


# Replace route handlers with wrapped versions
app.view_functions['get_workflows'] = async_route(get_workflows)
app.view_functions['get_workflow_schema'] = async_route(get_workflow_schema)
app.view_functions['execute_workflow'] = async_route(execute_workflow)
app.before_request_funcs = {None: [lambda: run_async(setup_service())]}
app.teardown_appcontext_funcs = [lambda e: run_async(cleanup_service(e))]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the PepperPy Playground web application")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind the server to")
    args = parser.parse_args()
    
    print(f"Starting PepperPy Playground on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True) 