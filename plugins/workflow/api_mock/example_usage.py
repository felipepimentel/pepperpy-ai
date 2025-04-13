#!/usr/bin/env python3
"""
Example script demonstrating the API Mock Server workflow.

This script shows how to use the API Mock Server workflow to create
and interact with a mock API server based on an OpenAPI specification.
"""

import asyncio
import json
import os
import yaml
from typing import Dict, Any

from pepperpy.workflow import create_workflow_provider


async def main() -> None:
    """Run the API Mock Server example."""
    print("API Mock Server Example")
    print("======================")
    
    # Load the sample OpenAPI specification
    script_dir = os.path.dirname(os.path.abspath(__file__))
    spec_path = os.path.join(script_dir, "sample_petstore.yaml")
    
    with open(spec_path, "r") as f:
        api_spec = yaml.safe_load(f)
    
    # Create the API Mock provider
    mock_provider = await create_workflow_provider(
        provider_name="api_mock",
        port=8080,
        host="localhost",
        persistence=True,
        validate_requests=True,
        generate_examples=True,
        verbose_logging=True
    )
    
    try:
        # Initialize the provider
        await mock_provider.initialize()
        
        # Create a mock server
        create_result = await mock_provider.execute({
            "action": "create",
            "api_spec": api_spec,
            "auto_start": True,
            "port": 8080
        })
        
        print(f"\nCreate Result: {json.dumps(create_result, indent=2)}")
        
        # Extract the server ID for future operations
        server_id = create_result.get("server_id")
        
        if not server_id:
            print("Failed to create mock server")
            return
        
        # Get server status
        status_result = await mock_provider.execute({
            "action": "status",
            "server_id": server_id
        })
        
        print(f"\nStatus Result: {json.dumps(status_result, indent=2)}")
        
        # At this point, the mock server is running and you can make real HTTP requests to it
        # In a real scenario, you would use tools like curl, requests, or other HTTP clients
        print(f"\nMock server is running at http://localhost:8080")
        print("You can make requests to the following endpoints:")
        print("- GET    /pets          - List all pets")
        print("- POST   /pets          - Create a pet")
        print("- GET    /pets/{id}     - Get a pet by ID")
        print("- PUT    /pets/{id}     - Update a pet")
        print("- DELETE /pets/{id}     - Delete a pet")
        print("- GET    /owners        - List all owners")
        print("- POST   /owners        - Create an owner")
        print("- GET    /owners/{id}   - Get an owner by ID")
        print("- GET    /owners/{id}/pets - List all pets for an owner")
        
        # Let the user interact with the server
        input("\nPress Enter to stop the server and exit...")
        
        # Stop the server
        stop_result = await mock_provider.execute({
            "action": "stop",
            "server_id": server_id
        })
        
        print(f"\nStop Result: {json.dumps(stop_result, indent=2)}")
        
    finally:
        # Clean up resources
        await mock_provider.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 