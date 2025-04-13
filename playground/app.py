#!/usr/bin/env python3
"""
PepperPy Playground - Web demonstration of PepperPy capabilities.

This application provides an interactive web interface to showcase
the various features and workflows of the PepperPy library.
"""

import os
import json
import uuid
import asyncio
import tempfile
from pathlib import Path
from functools import wraps
from typing import Dict, Any, List, Optional, Callable, Awaitable

from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename

from pepperpy import PepperPy
from pepperpy.core.logging import get_logger, configure_logging

# Import local workflow modules for direct access
from workflows import api_mock_workflow, a2a_simulation, api_governance_workflow
from .workflows import run_a2a_simulation, run_mock_api_server, execute_api_governance_workflow

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)

# Create Flask app
app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

# Global state
pp = None
sessions: Dict[str, Dict[str, Any]] = {}

def get_pepperpy():
    """Get or create the PepperPy instance."""
    global pp
    if pp is None:
        pp = PepperPy()
    return pp

def async_route(route_function):
    """Decorator to handle async route functions."""
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        return asyncio.run(route_function(*args, **kwargs))
    return wrapper

@app.route('/')
def index():
    """Render the main playground page."""
    return render_template('index.html')

@app.route('/api/session', methods=['POST'])
@async_route
async def create_session():
    """Create a new playground session."""
    global sessions
    
    # Initialize PepperPy if needed
    pepperpy = get_pepperpy()
    if not pepperpy.initialized:
        await pepperpy.initialize()
    
    # Create a session ID and workspace
    session_id = str(uuid.uuid4())
    workspace_dir = Path(tempfile.mkdtemp(prefix=f"pepperpy-playground-{session_id[:8]}-"))
    
    # Store session info
    sessions[session_id] = {
        "id": session_id,
        "workspace": str(workspace_dir),
        "created_at": int(os.path.getctime(workspace_dir)),
        "active_workflows": [],
        "resources": {}
    }
    
    logger.info(f"Created session {session_id} with workspace {workspace_dir}")
    
    return jsonify({
        "session_id": session_id,
        "workspace": str(workspace_dir)
    })

@app.route('/api/workflows', methods=['GET'])
@async_route
async def get_available_workflows():
    """Get a list of available workflows."""
    workflows = [
        {
            "id": "a2a_simulation",
            "name": "Agent-to-Agent Simulation",
            "description": "Run a simulation with multiple agents interacting with each other",
            "config_schema": {
                "type": "object",
                "properties": {
                    "num_agents": {
                        "type": "integer",
                        "description": "Number of agents in the simulation",
                        "default": 2
                    },
                    "max_turns": {
                        "type": "integer",
                        "description": "Maximum number of turns in the conversation",
                        "default": 10
                    },
                    "initial_message": {
                        "type": "string",
                        "description": "Message to start the conversation",
                        "default": "Hello, how are you?"
                    }
                }
            }
        },
        {
            "id": "api_mock",
            "name": "API Mock Server",
            "description": "Generate and run a mock API server based on an OpenAPI spec",
            "config_schema": {
                "type": "object",
                "properties": {
                    "spec_file": {
                        "type": "string",
                        "description": "Path to OpenAPI spec file or raw JSON/YAML content",
                        "default": ""
                    },
                    "port": {
                        "type": "integer",
                        "description": "Port to run the mock server on",
                        "default": 8000
                    }
                }
            }
        },
        {
            "id": "api_governance",
            "name": "API Governance Assessment",
            "description": "Analyze an API specification for governance and compliance issues",
            "config_schema": {
                "type": "object",
                "properties": {
                    "spec_file": {
                        "type": "string",
                        "description": "Path to OpenAPI spec file or raw JSON/YAML content",
                        "default": ""
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Format for the output report",
                        "enum": ["json", "markdown", "html"],
                        "default": "html"
                    }
                }
            }
        }
    ]
    
    return jsonify({"workflows": workflows})

@app.route('/api/workflow/<workflow_id>/schema', methods=['GET'])
@async_route
async def get_workflow_schema(workflow_id):
    """Get the schema for a specific workflow."""
    pepperpy = get_pepperpy()
    if not pepperpy.initialized:
        await pepperpy.initialize()
    
    # Example schemas for workflows
    schemas = {
        "api_mock": {
            "inputs": [
                {
                    "name": "action",
                    "type": "select",
                    "options": ["start_server", "stop_server", "list_servers", "get_server", "generate_client"],
                    "label": "Action",
                    "required": True
                },
                {
                    "name": "spec_path",
                    "type": "file",
                    "label": "OpenAPI Specification",
                    "required": True,
                    "conditions": {"action": "start_server"},
                    "file_types": [".yaml", ".yml", ".json"]
                },
                {
                    "name": "port",
                    "type": "number",
                    "label": "Port",
                    "required": False,
                    "default": 8080,
                    "conditions": {"action": "start_server"}
                },
                {
                    "name": "server_id",
                    "type": "string",
                    "label": "Server ID",
                    "required": True,
                    "conditions": {"action": ["stop_server", "get_server", "generate_client"]}
                },
                {
                    "name": "language",
                    "type": "select",
                    "options": ["python", "javascript", "typescript", "java", "csharp"],
                    "label": "Client Language",
                    "required": True,
                    "conditions": {"action": "generate_client"}
                },
                {
                    "name": "output_dir",
                    "type": "string",
                    "label": "Output Directory",
                    "required": True,
                    "conditions": {"action": "generate_client"}
                }
            ],
            "outputs": {
                "start_server": [
                    {"name": "server", "type": "object", "label": "Server Information"}
                ],
                "stop_server": [
                    {"name": "success", "type": "boolean", "label": "Success"}
                ],
                "list_servers": [
                    {"name": "servers", "type": "array", "label": "Server List"}
                ],
                "get_server": [
                    {"name": "server", "type": "object", "label": "Server Information"}
                ],
                "generate_client": [
                    {"name": "success", "type": "boolean", "label": "Success"},
                    {"name": "output_dir", "type": "string", "label": "Output Directory"}
                ]
            }
        },
        "api_blueprint": {
            "inputs": [
                {
                    "name": "user_stories",
                    "type": "text",
                    "label": "User Stories",
                    "required": True,
                    "placeholder": "As a user, I want to... so that..."
                },
                {
                    "name": "output_format",
                    "type": "select",
                    "options": ["openapi", "json_schema", "raml", "postman"],
                    "label": "Output Format",
                    "required": True,
                    "default": "openapi"
                },
                {
                    "name": "generate_code",
                    "type": "boolean",
                    "label": "Generate Code",
                    "default": true
                },
                {
                    "name": "language",
                    "type": "select",
                    "options": ["python", "javascript", "typescript", "java", "csharp"],
                    "label": "Programming Language",
                    "conditions": {"generate_code": true},
                    "default": "python"
                }
            ],
            "outputs": [
                {"name": "api_spec", "type": "object", "label": "API Specification"},
                {"name": "documentation", "type": "string", "label": "Documentation"},
                {"name": "code", "type": "object", "label": "Generated Code"}
            ]
        },
        "api_governance": {
            "inputs": [
                {
                    "name": "api_spec",
                    "type": "file",
                    "label": "API Specification",
                    "required": True,
                    "file_types": [".yaml", ".yml", ".json"]
                },
                {
                    "name": "governance_rules",
                    "type": "select",
                    "options": ["security", "standards", "performance", "all"],
                    "label": "Governance Rules",
                    "required": True,
                    "default": "all"
                },
                {
                    "name": "output_format",
                    "type": "select",
                    "options": ["json", "html", "markdown", "pdf"],
                    "label": "Output Format",
                    "required": True,
                    "default": "json"
                }
            ],
            "outputs": [
                {"name": "report", "type": "object", "label": "Governance Report"},
                {"name": "compliance_score", "type": "number", "label": "Compliance Score"},
                {"name": "recommendations", "type": "array", "label": "Recommendations"}
            ]
        },
        "a2a_demo": {
            "inputs": [
                {
                    "name": "scenario",
                    "type": "select",
                    "options": ["simple_conversation", "stateful_interaction", "multi_agent_collaboration"],
                    "label": "Scenario",
                    "required": True,
                    "default": "simple_conversation"
                },
                {
                    "name": "agent_count",
                    "type": "number",
                    "label": "Number of Agents",
                    "required": True,
                    "default": 2,
                    "min": 2,
                    "max": 10
                },
                {
                    "name": "initial_message",
                    "type": "text",
                    "label": "Initial Message",
                    "required": True,
                    "placeholder": "Enter a message to start the conversation..."
                }
            ],
            "outputs": [
                {"name": "conversation", "type": "array", "label": "Conversation"},
                {"name": "agents", "type": "array", "label": "Agent Information"}
            ]
        }
    }
    
    if workflow_id not in schemas:
        return jsonify({"error": f"Schema for workflow '{workflow_id}' not found"}), 404
    
    return jsonify(schemas[workflow_id])

@app.route('/api/samples/<workflow_id>', methods=['GET'])
def get_workflow_samples(workflow_id):
    """Get sample data for a specific workflow."""
    samples = {
        "api_mock": {
            "petstore": {
                "name": "Pet Store API",
                "spec": Path("workflows/sample_petstore.yaml").read_text() if Path("workflows/sample_petstore.yaml").exists() else ""
            }
        },
        "api_blueprint": {
            "todo_app": {
                "name": "Todo App API",
                "user_stories": """
As a user, I want to create a new todo item with a title and optional description.
As a user, I want to list all my todo items.
As a user, I want to mark a todo item as completed.
As a user, I want to update the title or description of a todo item.
As a user, I want to delete a todo item.
As a user, I want to filter todo items by completion status.
                """
            },
            "blog_api": {
                "name": "Blog API",
                "user_stories": """
As a blogger, I want to create blog posts with a title, content, and optional tags.
As a blogger, I want to list all my published and draft posts.
As a reader, I want to view published blog posts.
As a reader, I want to add comments to blog posts.
As a blogger, I want to moderate comments on my posts.
As a user, I want to search for blog posts by title or content.
                """
            }
        },
        "api_governance": {
            "sample_api": {
                "name": "Sample API",
                "governance_rules": "all"
            }
        },
        "a2a_demo": {
            "simple_chat": {
                "name": "Simple Chat",
                "scenario": "simple_conversation",
                "agent_count": 2,
                "initial_message": "Hello, I'd like to know more about PepperPy's agent-to-agent capabilities."
            },
            "stateful_chat": {
                "name": "Stateful Interaction",
                "scenario": "stateful_interaction",
                "agent_count": 2,
                "initial_message": "I'd like to plan a trip to Paris. Can you help me?"
            }
        }
    }
    
    if workflow_id not in samples:
        return jsonify({"error": f"Samples for workflow '{workflow_id}' not found"}), 404
    
    return jsonify({"samples": samples[workflow_id]})

@app.route('/api/workflow/<workflow_id>/execute', methods=['POST'])
@async_route
async def execute_workflow(workflow_id):
    """Execute a workflow with the provided inputs."""
    session_id = request.json.get('session_id')
    inputs = request.json.get('inputs', {})
    
    if not session_id or session_id not in sessions:
        return jsonify({"error": "Invalid session ID"}), 400
    
    session = sessions[session_id]
    
    # Initialize PepperPy if needed
    pepperpy = get_pepperpy()
    if not pepperpy.initialized:
        await pepperpy.initialize()
    
    try:
        # Execute based on workflow ID
        result = None
        
        if workflow_id == "api_mock":
            # Use the local API Mock workflow module
            result = await api_mock_workflow.execute_workflow(inputs, session['workspace'])
        elif workflow_id == "a2a_demo":
            # Use the local A2A simulation module
            result = await a2a_simulation.execute_simulation(inputs)
        else:
            # Try to get the workflow provider from PepperPy plugins
            try:
                provider = pepperpy.get_plugin(plugin_type="workflow", provider_name=workflow_id)
                if not provider:
                    return jsonify({"error": f"Workflow '{workflow_id}' not found"}), 404
                
                # Save any uploaded files
                file_inputs = {}
                for key, value in inputs.items():
                    if key.endswith('_file') and value.startswith('data:'):
                        # Handle file upload
                        file_path = await save_file_from_data_url(value, session['workspace'], key)
                        file_inputs[key.replace('_file', '')] = file_path
                
                # Combine regular inputs with file paths
                execute_inputs = {**inputs, **file_inputs}
                
                # Execute the workflow via provider
                result = await provider.execute(execute_inputs)
            except Exception as e:
                logger.error(f"Error getting workflow provider: {str(e)}")
                return jsonify({"error": f"Error getting workflow provider: {str(e)}"}), 500
        
        if result is None:
            return jsonify({"error": "Workflow execution returned no result"}), 500
        
        # Add the workflow to the session's active workflows
        active_workflow = {
            "id": workflow_id,
            "inputs": inputs,
            "result": result,
            "timestamp": get_current_timestamp()
        }
        session['active_workflows'].append(active_workflow)
        
        return jsonify({
            "success": True,
            "result": result,
            "workflow_id": workflow_id
        })
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "workflow_id": workflow_id
        }), 500

async def save_file_from_data_url(data_url, workspace, filename_prefix):
    """Save a file from a data URL to the session workspace."""
    import base64
    
    # Extract content type and base64 data
    content_parts = data_url.split(',')
    if len(content_parts) != 2 or ';base64' not in content_parts[0]:
        raise ValueError("Invalid data URL format")
    
    # Determine file extension from content type
    content_type = content_parts[0].split(':')[1].split(';')[0]
    ext = ''
    if content_type == 'application/json':
        ext = '.json'
    elif content_type in ('application/x-yaml', 'text/yaml'):
        ext = '.yaml'
    else:
        ext = '.' + content_type.split('/')[-1]
    
    # Decode base64 data
    file_data = base64.b64decode(content_parts[1])
    
    # Create workspace directory if it doesn't exist
    workspace_path = Path(workspace)
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Create a unique filename
    filename = f"{filename_prefix}_{uuid.uuid4().hex}{ext}"
    file_path = workspace_path / filename
    
    # Write file data
    with open(file_path, 'wb') as f:
        f.write(file_data)
    
    return str(file_path)

def get_current_timestamp():
    """Get the current timestamp in seconds."""
    import time
    return int(time.time())

@app.route('/api/session/<session_id>/resources', methods=['GET'])
def get_session_resources(session_id):
    """Get all resources for a session."""
    if session_id not in sessions:
        return jsonify({"error": "Invalid session ID"}), 400
    
    session = sessions[session_id]
    return jsonify({"resources": session.get('resources', {})})

@app.route('/api/session/<session_id>/clean', methods=['POST'])
@async_route
async def clean_session(session_id):
    """Clean up a session's resources."""
    global sessions
    
    if session_id not in sessions:
        return jsonify({"error": "Invalid session ID"}), 400
    
    session = sessions[session_id]
    
    # Delete the workspace directory
    workspace_path = Path(session['workspace'])
    if workspace_path.exists():
        import shutil
        shutil.rmtree(workspace_path)
    
    # Remove the session
    del sessions[session_id]
    
    return jsonify({"success": True})

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files from the static directory."""
    return send_from_directory('static', path)

@app.before_first_request
def init_app():
    """Initialize the application."""
    # Create necessary directories
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('workflows', exist_ok=True)

# Cleanup function to be called at application exit
def cleanup():
    """Clean up application resources."""
    global pp, sessions
    
    # Close PepperPy instance
    if pp and pp.initialized:
        asyncio.run(pp.cleanup())
        pp = None
    
    # Clean up session workspaces
    for session_id, session in list(sessions.items()):
        workspace_path = Path(session['workspace'])
        if workspace_path.exists():
            import shutil
            shutil.rmtree(workspace_path)
    
    sessions = {}

# Register cleanup function at application exit
import atexit
atexit.register(cleanup)

@app.route('/workflows', methods=['GET'])
def get_workflows():
    """Return available workflows for the playground."""
    return jsonify({
        "workflows": [
            {
                "id": "api_mock",
                "name": "API Mock Workflow",
                "description": "Mock API endpoints from OpenAPI specifications",
                "path": "/workflows/api-mock"
            },
            {
                "id": "a2a_simulation",
                "name": "A2A Simulation",
                "description": "Simulate Agent-to-Agent communications",
                "path": "/workflows/a2a-simulation"
            },
            {
                "id": "api_governance",
                "name": "API Governance",
                "description": "Assess API specifications against governance rules",
                "path": "/workflows/api-governance"
            }
        ]
    })

@app.route('/workflows/api-governance', methods=['GET', 'POST'])
def api_governance():
    """Handle API governance workflow requests."""
    if request.method == 'GET':
        return render_template('api_governance.html')
    
    # Process API governance request
    files = request.files
    if 'api_spec' not in files:
        return jsonify({"error": "No API specification file provided"}), 400
    
    api_spec_file = files['api_spec']
    
    # Save uploaded file to temporary location
    temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(api_spec_file.filename))
    api_spec_file.save(temp_file_path)
    
    # Get output format
    output_format = request.form.get('output_format', 'json')
    if output_format not in ['json', 'markdown', 'html', 'pdf']:
        output_format = 'json'
    
    try:
        # Execute governance workflow
        result = api_governance_workflow.execute_workflow(
            api_spec_path=temp_file_path,
            output_format=output_format
        )
        
        # Clean up temporary file
        os.remove(temp_file_path)
        
        return jsonify(result)
    except Exception as e:
        # Clean up temporary file in case of error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return jsonify({"error": str(e)}), 500

@app.route('/api/run_workflow', methods=['POST'])
def run_workflow():
    workflow_id = request.json.get('workflow_id')
    config = request.json.get('config', {})
    
    if workflow_id == 'a2a_simulation':
        result = run_a2a_simulation(
            num_agents=config.get('num_agents', 2),
            max_turns=config.get('max_turns', 10),
            initial_message=config.get('initial_message', 'Hello, how are you?')
        )
        return jsonify({"result": result})
    
    elif workflow_id == 'api_mock':
        spec_content = config.get('spec_file', '')
        port = config.get('port', 8000)
        
        # If content is provided directly, save to a temporary file
        if spec_content and not os.path.isfile(spec_content):
            with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp:
                temp.write(spec_content.encode('utf-8'))
                spec_file = temp.name
        else:
            # Use the provided file path or default to sample
            spec_file = spec_content if os.path.isfile(spec_content) else 'playground/workflows/sample_petstore.yaml'
        
        result = run_mock_api_server(spec_file=spec_file, port=port)
        return jsonify({"result": result})
    
    elif workflow_id == 'api_governance':
        spec_content = config.get('spec_file', '')
        output_format = config.get('output_format', 'html')
        
        # If content is provided directly, save to a temporary file
        if spec_content and not os.path.isfile(spec_content):
            with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp:
                temp.write(spec_content.encode('utf-8'))
                spec_file = temp.name
        else:
            # Use the provided file path or default to sample
            spec_file = spec_content if os.path.isfile(spec_content) else 'playground/workflows/sample_petstore.yaml'
        
        result = execute_api_governance_workflow(api_spec_path=spec_file, output_format=output_format)
        
        # For JSON format, return directly
        if output_format == 'json':
            return jsonify({"result": result})
        # For other formats (markdown, html), return as string
        else:
            return jsonify({"result": result})
    
    else:
        return jsonify({"error": f"Unknown workflow: {workflow_id}"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port) 