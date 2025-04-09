# MCP Demo Workflow

This workflow demonstrates the complete integration of Model Context Protocol (MCP) server and client components.

## Features

- Start an MCP server with the specified configuration
- Register demo tools (calculate, weather, translate)
- Handle client requests through the MCP protocol
- Simulate or run real client requests for demonstration

## Usage

Run the workflow with:

```bash
# Basic usage with simulated results
python -m pepperpy.cli workflow run workflow/mcp_demo

# Run with real client-server interaction
python -m pepperpy.cli workflow run workflow/mcp_demo --config '{"run_real_demo": true}'

# With OpenAI API key
OPENAI_API_KEY=your_key_here python -m pepperpy.cli workflow run workflow/mcp_demo
```

## CLI Tool

A command-line interface is provided for interacting with a running MCP server:

```bash
# Connect to the local MCP server
python plugins/workflow/mcp_demo/cli.py

# Connect to a remote server
python plugins/workflow/mcp_demo/cli.py --host api.example.com --port 443
```

The CLI tool supports these commands:

- `/help` - Show help information
- `/quit` or `/exit` - Exit the CLI
- `/clear` - Clear conversation history
- `/models` - List available models
- `/model <model_id>` - Change the current model
- `/calc <expression>` - Use the calculate tool
- `/weather <location>` - Use the weather tool
- `/translate <text> to <language>` - Use the translate tool

For any other input, the CLI will send it as a chat message to the AI.

## Standalone Server

A standalone server script is also provided for development and testing purposes:

```bash
# Start the server with default settings
python plugins/workflow/mcp_demo/run_server.py

# Configure host and port
python plugins/workflow/mcp_demo/run_server.py --host localhost --port 8080

# Use a specific LLM model
python plugins/workflow/mcp_demo/run_server.py --llm-model gpt-4
```

Use this script when you want to run just the server component without the complete workflow. Combined with the CLI, you can develop and test MCP integrations easily.

## Combined Command-Line Tool

A unified command-line tool is also available that combines all the functionality:

```bash
# Run just the server
python plugins/workflow/mcp_demo/mcp.py server --port 8080

# Run just the client
python plugins/workflow/mcp_demo/mcp.py client --host api.example.com

# Run the complete workflow
python plugins/workflow/mcp_demo/mcp.py workflow --llm-model gpt-4 --duration 120
```

This tool provides a convenient interface for running any component of the MCP demo.

## Configuration

You can customize the workflow with these parameters:

```yaml
host: "0.0.0.0"          # Host address to bind the server to
port: 8000               # Port for the MCP server
provider_type: "http"    # Type of MCP provider to use
llm_provider: "openai"   # LLM provider to use
llm_model: "gpt-3.5-turbo" # LLM model to use
demo_duration: 60        # Duration in seconds to run the demo
```

## Demo Tools

The workflow demonstrates these MCP tool integrations:

- **Chat**: Basic conversation with LLM model
- **Calculate**: Evaluate mathematical expressions (format: `calculate: 2 + 2`)
- **Weather**: Get weather information for a location (format: `get_weather: London`)
- **Translate**: Translate text to another language (format: `translate: Hello world to es`)

## Examples

### Basic Chat

```
> Hello, how are you?
AI: I'm doing well, thank you for asking! I'm here to assist you. How can I help you today?
```

### Using Calculate Tool

```
> /calc 2 + 2 * 3
Result: 8
```

### Using Weather Tool

```
> /weather New York
Weather for New York:
  Temperature: 20°C
  Condition: sunny
```

### Using Translate Tool 

```
> /translate Hello world to es
Translation: [es] Hola mundo
```

## Summary

The MCP Demo workflow demonstrates the following key concepts:

1. **Server-Client Architecture**: Implementation of both MCP server and client components
2. **Tool Registration**: How to register custom tools with an MCP server
3. **Multiple Interfaces**: Different ways to run and interact with MCP components:
   - Full workflow through PepperPy CLI
   - Standalone server for external clients
   - Interactive client CLI for direct testing
   - Combined command-line tool for all components
4. **Protocol Integration**: Complete implementation of the Model Context Protocol
5. **LLM Integration**: Integration with OpenAI or other LLM providers
6. **Error Handling**: Proper error handling throughout the protocol stack

Use this demo as a reference implementation for building your own MCP integrations or extending existing ones. 