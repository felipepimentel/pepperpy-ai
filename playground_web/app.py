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

from flask import Flask, render_template, request, jsonify, after_this_request
from flask_cors import CORS

# Local imports
from mock_api_service import MockWorkflowService

app = Flask(__name__)
CORS(app)

# Create a global workflow service instance
workflow_service = MockWorkflowService()
initialized = False


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


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "PepperPy Playground Web",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/workflows', methods=['GET'])
async def get_workflows():
    """Get available workflows."""
    try:
        workflows = await workflow_service.get_available_workflows()
        return jsonify({"workflows": workflows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/workflow/<workflow_id>/schema', methods=['GET'])
async def get_workflow_schema(workflow_id):
    """Get schema for a specific workflow."""
    try:
        workflow = await workflow_service.get_workflow_schema(workflow_id)
        return jsonify(workflow)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/workflow/<workflow_id>/execute', methods=['POST'])
async def execute_workflow(workflow_id):
    """Execute a workflow."""
    try:
        data = request.json or {}
        input_data = data.get('input_data', {})
        config = data.get('config', {})
        
        result = await workflow_service.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            config=config
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/samples/<workflow_id>', methods=['GET'])
def get_workflow_samples(workflow_id):
    """Get sample inputs for a workflow."""
    # Return sample data based on workflow ID
    samples = {
        "api_governance": {
            "input_data": {
                "api_spec": {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "Sample API",
                        "version": "1.0.0"
                    },
                    "paths": {
                        "/users": {
                            "get": {
                                "summary": "Get users"
                            }
                        }
                    }
                },
                "output_format": "json",
                "rule_set": "default"
            },
            "config": {
                "output_format": "json",
                "llm_config": {
                    "provider": "openai",
                    "model": "gpt-4"
                }
            }
        },
        "api_blueprint": {
            "input_data": {
                "user_stories": [
                    "As a user, I want to be able to create an account",
                    "As a user, I want to be able to login to my account",
                    "As a user, I want to be able to view my profile"
                ],
                "output_format": "openapi",
                "target_tech": "node"
            },
            "config": {
                "llm_config": {
                    "provider": "openai",
                    "model": "gpt-4"
                }
            }
        },
        "api_mock": {
            "input_data": {
                "api_spec": {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "Sample API",
                        "version": "1.0.0"
                    },
                    "paths": {
                        "/users": {
                            "get": {
                                "summary": "Get users",
                                "responses": {
                                    "200": {
                                        "description": "Success"
                                    }
                                }
                            }
                        }
                    }
                },
                "port": 8080,
                "response_delay": 0
            }
        },
        "api_evolution": {
            "input_data": {
                "current_api": {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "Current API",
                        "version": "1.0.0"
                    },
                    "paths": {
                        "/users": {
                            "get": {
                                "summary": "Get users"
                            }
                        }
                    }
                },
                "proposed_api": {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "Proposed API",
                        "version": "2.0.0"
                    },
                    "paths": {
                        "/users": {
                            "get": {
                                "summary": "Get users",
                                "parameters": [
                                    {
                                        "name": "limit",
                                        "in": "query",
                                        "required": False
                                    }
                                ]
                            }
                        },
                        "/users/{id}": {
                            "get": {
                                "summary": "Get user by ID"
                            }
                        }
                    }
                },
                "output_format": "json"
            }
        },
        "api_ready": {
            "input_data": {
                "spec_path": "/static/samples/petstore.yaml",
                "enhancement_options": {
                    "agent_discovery": True,
                    "auth_mechanism": "api_key",
                    "observability": True,
                    "rate_limiting": True,
                    "documentation": True
                },
                "output_dir": "/tmp"
            },
            "config": {
                "llm_config": {
                    "provider": "openai",
                    "model": "gpt-4"
                }
            }
        }
    }
    
    if workflow_id not in samples:
        return jsonify({"error": "No samples found for this workflow"}), 404
        
    return jsonify(samples[workflow_id])


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