#!/usr/bin/env python3
"""
API Mock Workflow.

This module provides functionality to create and manage mock API servers
based on OpenAPI specifications.
"""

import os
import json
import asyncio
import uuid
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from pepperpy import PepperPy
from pepperpy.core.logging import get_logger, configure_logging

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)

# Sample OpenAPI specification
SAMPLE_OPENAPI_SPEC = """
openapi: 3.0.0
info:
  title: Sample Petstore API
  version: 1.0.0
  description: A sample API for managing pets
paths:
  /pets:
    get:
      summary: List all pets
      operationId: listPets
      responses:
        '200':
          description: An array of pets
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Pet'
    post:
      summary: Create a pet
      operationId: createPet
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NewPet'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Pet'
  /pets/{petId}:
    get:
      summary: Get a pet by ID
      operationId: getPet
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: A pet
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Pet'
        '404':
          description: Pet not found
components:
  schemas:
    Pet:
      type: object
      required:
        - id
        - name
      properties:
        id:
          type: integer
        name:
          type: string
        tag:
          type: string
    NewPet:
      type: object
      required:
        - name
      properties:
        name:
          type: string
        tag:
          type: string
"""

async def execute_workflow(inputs: Dict[str, Any], workspace_dir: str) -> Dict[str, Any]:
    """
    Execute the API Mock workflow.
    
    Args:
        inputs: The workflow inputs
        workspace_dir: The directory for workspace files
        
    Returns:
        The workflow result
    """
    action = inputs.get('action')
    
    if not action:
        return {"error": "No action specified"}
    
    if action == "start_server":
        return await start_mock_server(inputs, workspace_dir)
    elif action == "stop_server":
        return await stop_mock_server(inputs)
    elif action == "list_servers":
        return await list_mock_servers()
    elif action == "get_server":
        return await get_mock_server(inputs)
    elif action == "generate_client":
        return await generate_client(inputs)
    else:
        return {"error": f"Unknown action: {action}"}

# Keep track of running servers
MOCK_SERVERS = {}

async def start_mock_server(inputs: Dict[str, Any], workspace_dir: str) -> Dict[str, Any]:
    """Start a mock API server."""
    spec_path = inputs.get('spec_path')
    if not spec_path:
        return {"error": "No OpenAPI specification provided"}
    
    port = inputs.get('port', 8080)
    
    # Create a server ID
    server_id = str(uuid.uuid4())
    
    # If spec_path is uploaded file data, save it to workspace
    if isinstance(spec_path, str) and spec_path.startswith('data:'):
        spec_path = await save_spec_file(spec_path, workspace_dir)
    
    # Start mock server with Prism (or similar tool)
    server_process = await start_prism_server(spec_path, port)
    
    # Store server information
    MOCK_SERVERS[server_id] = {
        "id": server_id,
        "spec_path": spec_path,
        "port": port,
        "process": server_process,
        "status": "running"
    }
    
    # Return server info (without process)
    server_info = MOCK_SERVERS[server_id].copy()
    del server_info["process"]
    
    return {"server": server_info}

async def save_spec_file(data_url: str, workspace_dir: str) -> str:
    """Save OpenAPI spec from data URL to a file."""
    import base64
    
    # Extract content type and base64 data
    content_parts = data_url.split(',')
    if len(content_parts) != 2 or ';base64' not in content_parts[0]:
        raise ValueError("Invalid data URL format")
    
    # Determine file extension from content type
    content_type = content_parts[0].split(':')[1].split(';')[0]
    ext = '.yaml'
    if content_type == 'application/json':
        ext = '.json'
    
    # Decode base64 data
    file_data = base64.b64decode(content_parts[1])
    
    # Create a unique filename in the workspace
    filename = f"openapi_spec_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(workspace_dir, filename)
    
    # Write file data
    with open(file_path, 'wb') as f:
        f.write(file_data)
    
    return file_path

async def start_prism_server(spec_path: str, port: int) -> subprocess.Popen:
    """Start a Prism server for the given spec."""
    # Check if prism is installed
    try:
        await asyncio.create_subprocess_exec("prism", "--version")
    except Exception:
        # Prism not found, simulate server for demonstration
        return None
    
    # In a real implementation, we would start prism:
    # process = await asyncio.create_subprocess_exec(
    #     "prism", "mock", spec_path,
    #     "--port", str(port),
    #     stdout=asyncio.subprocess.PIPE
    # )
    
    # For demo purposes, we'll simulate a server process
    process = None
    
    return process

async def stop_mock_server(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Stop a running mock server."""
    server_id = inputs.get('server_id')
    if not server_id:
        return {"error": "No server ID provided"}
    
    if server_id not in MOCK_SERVERS:
        return {"error": f"Server with ID {server_id} not found"}
    
    server = MOCK_SERVERS[server_id]
    
    if server["status"] != "running":
        return {"error": "Server is not running"}
    
    # Terminate the process
    process = server["process"]
    if process:
        process.terminate()
    
    # Update server status
    MOCK_SERVERS[server_id]["status"] = "stopped"
    
    return {"success": True}

async def list_mock_servers() -> Dict[str, Any]:
    """List all mock servers."""
    # Return servers without process information
    servers = []
    for server_id, server in MOCK_SERVERS.items():
        server_info = server.copy()
        if "process" in server_info:
            del server_info["process"]
        servers.append(server_info)
    
    return {"servers": servers}

async def get_mock_server(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Get information about a specific mock server."""
    server_id = inputs.get('server_id')
    if not server_id:
        return {"error": "No server ID provided"}
    
    if server_id not in MOCK_SERVERS:
        return {"error": f"Server with ID {server_id} not found"}
    
    # Return server without process information
    server_info = MOCK_SERVERS[server_id].copy()
    if "process" in server_info:
        del server_info["process"]
    
    return {"server": server_info}

async def generate_client(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate client code for a mock server."""
    server_id = inputs.get('server_id')
    language = inputs.get('language')
    output_dir = inputs.get('output_dir')
    
    if not server_id or not language or not output_dir:
        return {"error": "Missing required parameters"}
    
    if server_id not in MOCK_SERVERS:
        return {"error": f"Server with ID {server_id} not found"}
    
    server = MOCK_SERVERS[server_id]
    spec_path = server["spec_path"]
    
    # In a real implementation, we would use OpenAPI Generator or similar
    # For demo purposes, return a sample result
    
    return {
        "success": True,
        "output_dir": output_dir,
        "language": language,
        "files": [
            {"name": "api_client.py", "path": f"{output_dir}/api_client.py"},
            {"name": "models.py", "path": f"{output_dir}/models.py"},
            {"name": "api.py", "path": f"{output_dir}/api.py"}
        ]
    }

async def main():
    """Run the API Mock workflow example."""
    # Initialize PepperPy
    pp = PepperPy()
    await pp.initialize()
    
    try:
        # Create a temporary OpenAPI specification file
        temp_dir = Path("./tmp/api_mock_example")
        os.makedirs(temp_dir, exist_ok=True)
        spec_path = temp_dir / "petstore.yaml"
        
        with open(spec_path, "w") as f:
            f.write(SAMPLE_OPENAPI_SPEC)
        
        logger.info(f"Created OpenAPI specification at {spec_path}")
        
        # Get the API Mock workflow provider
        api_mock = pp.get_plugin(plugin_type="workflow", provider_name="api_mock")
        
        # Start a mock server
        start_result = await api_mock.execute({
            "action": "start_server",
            "spec_path": str(spec_path)
        })
        
        server_id = start_result["server_id"]
        server_url = start_result["url"]
        
        logger.info(f"Started mock server with ID {server_id} at {server_url}")
        
        # List all running servers
        list_result = await api_mock.execute({"action": "list_servers"})
        
        logger.info(f"Running servers: {json.dumps(list_result, indent=2)}")
        
        # Generate a Python client for the mock server
        generate_result = await api_mock.execute({
            "action": "generate_client",
            "server_id": server_id,
            "language": "python",
            "output_file": str(temp_dir / "petstore_client.py")
        })
        
        logger.info(f"Generated client at {generate_result.get('output_file')}")
        
        # Wait a moment to demonstrate the server running
        logger.info(f"Mock server is running at {server_url}. Press Ctrl+C to stop...")
        await asyncio.sleep(5)
        
        # Stop the mock server
        stop_result = await api_mock.execute({
            "action": "stop_server",
            "server_id": server_id
        })
        
        logger.info(f"Stopped mock server with ID {server_id}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        # Clean up PepperPy resources
        await pp.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Example stopped by user") 