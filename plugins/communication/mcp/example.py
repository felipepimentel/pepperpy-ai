#!/usr/bin/env python3
"""
Example of using the MCP plugin with the official MCP library.

This script demonstrates how to use the PepperPy MCP plugin to:
1. Set up a simple MCP server
2. Create a client that connects to the server
3. Define and call tools on the server
"""

import asyncio
import logging
from typing import Dict, Any

from pepperpy import PepperPy
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_example")

# Sample MCP server using the official library directly
def create_sample_server():
    """Create a sample MCP server using the official library directly."""
    server = FastMCP("Sample Server")
    
    @server.tool()
    def greeting(name: str) -> str:
        """Create a greeting for a person."""
        return f"Hello, {name}! Welcome to the MCP world."
    
    @server.resource("sample://data/{id}")
    def sample_data(id: str) -> str:
        """Get sample data by ID."""
        samples = {
            "1": "This is sample data #1",
            "2": "This is sample data #2",
            "3": "This is sample data #3"
        }
        return samples.get(id, f"No sample found with ID {id}")
    
    return server

# Example of using MCP client through PepperPy
async def run_mcp_client():
    """Run an MCP client using the PepperPy MCP plugin."""
    logger.info("Initializing PepperPy with MCP client")
    
    pepperpy = PepperPy().with_mcp_client("http",
        server_url="http://localhost:8000"
    )
    
    # Initialize plugin
    await pepperpy.initialize()
    
    try:
        # Call the greeting tool
        logger.info("Calling the greeting tool...")
        result = await pepperpy.mcp_client.call_tool("greeting", {"name": "PepperPy User"})
        logger.info(f"Greeting result: {result}")
        
        # Read a sample resource
        logger.info("Reading a sample resource...")
        content, mime_type = await pepperpy.mcp_client.read_resource("sample://data/1")
        logger.info(f"Resource content: {content.decode()}, MIME type: {mime_type}")
        
    finally:
        # Clean up
        await pepperpy.cleanup()

async def main():
    """Main function demonstrating MCP server and client."""
    logger.info("Starting MCP example")
    
    # Create and run the server in a separate process
    import multiprocessing
    
    def run_server():
        server = create_sample_server()
        server.run(host="127.0.0.1", port=8000)
    
    # Start the server process
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    
    try:
        # Give the server a moment to start
        logger.info("Waiting for server to start...")
        await asyncio.sleep(2)
        
        # Run the client
        await run_mcp_client()
        
    finally:
        # Terminate the server process
        server_process.terminate()
        server_process.join()
    
    logger.info("MCP example completed")

if __name__ == "__main__":
    asyncio.run(main()) 