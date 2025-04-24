# PepperPy MCP Plugin

This plugin implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) for the PepperPy framework, using the official MCP Python library as a wrapper.

## Overview

The Model Context Protocol (MCP) is an open standard that enables AI systems (like large language models) to connect to external data sources and tools through a standardized interface. This plugin allows PepperPy to communicate with MCP servers and clients.

## Architecture

The MCP plugin consists of:

1. **MCP Communication Adapter**: Core adapter that implements the PepperPy communication interface using the official MCP library.
2. **HTTP Server**: Implementation of an HTTP-based MCP server using the FastMCP class from the official library.
3. **HTTP Client**: Implementation of an HTTP-based MCP client using the ClientSession from the official library.

## Installation

The plugin is included in the PepperPy framework. To use it, ensure you have the official MCP library installed:

```bash
pip install mcp
```

## Usage

### Using the MCP Communication Adapter

```python
from pepperpy import PepperPy

# Initialize PepperPy with MCP adapter
pepperpy = PepperPy().with_communication("mcp", 
    base_url="http://localhost:8000", 
    api_key="your-api-key"
)

# Send a message
message = pepperpy.communication.create_message(receiver="recipient", text="Hello!")
message_id = await pepperpy.communication.send_message(message)

# Receive a message
response = await pepperpy.communication.receive_message(message_id)
```

### Using the MCP Server

```python
from pepperpy import PepperPy

# Initialize PepperPy with MCP HTTP server
pepperpy = PepperPy().with_mcp_server("http", 
    server_name="My MCP Server",
    port=8000, 
    host="127.0.0.1"
)

# Add tools and resources to the server
@pepperpy.mcp_server.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# Run the server
pepperpy.mcp_server.run()
```

### Using the MCP Client

```python
from pepperpy import PepperPy

# Initialize PepperPy with MCP HTTP client
pepperpy = PepperPy().with_mcp_client("http", 
    server_url="http://localhost:8000"
)

# Call a tool on the server
result = await pepperpy.mcp_client.call_tool("add", {"a": 1, "b": 2})
print(result)  # Output: 3
```

## Configuration

### MCP Communication Adapter

| Parameter | Description | Default |
|-----------|-------------|---------|
| base_url | Base URL for the MCP server | http://localhost:8000 |
| api_key | API key for authentication | "" |
| timeout | Request timeout in seconds | 30 |
| headers | Additional headers to include in requests | {} |

### MCP HTTP Server

| Parameter | Description | Default |
|-----------|-------------|---------|
| server_name | Name of the MCP server | PepperPy MCP Server |
| port | Port to listen on | 8000 |
| host | Host address to bind to | 127.0.0.1 |

### MCP HTTP Client

| Parameter | Description | Default |
|-----------|-------------|---------|
| server_url | URL of the MCP server | http://localhost:8000 |

## License

This plugin is part of the PepperPy framework and is licensed under the MIT license. 