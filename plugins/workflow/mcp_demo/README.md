# MCP Demo Workflow

This workflow demonstrates the integration of Model Context Protocol (MCP) server and client components in PepperPy.

## Overview

The MCP Demo Workflow provides a simplified example of how to:

1. Initialize and run an MCP server
2. Register custom tools with the server
3. Connect an MCP client to interact with the server
4. Send different types of requests through the MCP protocol

## Features

The demo includes the following functionality:

- **Chat**: Basic LLM conversation via an OpenAI model
- **Calculate**: A simple tool to evaluate mathematical expressions
- **Weather**: A mock tool to retrieve weather information for locations
- **Translate**: A simulated translation tool

## Running the Demo

To run the demo workflow:

```bash
# Basic usage
python -m pepperpy.cli workflow run workflow/mcp_demo

# With explicit OpenAI API key
OPENAI_API_KEY=your_key_here python -m pepperpy.cli workflow run workflow/mcp_demo
```

## CLI Tool

A command-line interface is provided for interactive testing with a running MCP server:

```bash
# Connect to the local MCP server (default: localhost:8042)
python plugins/workflow/mcp_demo/cli.py

# Connect to a specific server
python plugins/workflow/mcp_demo/cli.py --host example.com --port 443
```

Available commands in the CLI:

- `/help` - Show help information
- `/quit` or `/exit` - Exit the CLI
- `/clear` - Clear conversation history
- `/models` - List available models (if supported by server)
- `/calc <expression>` - Use the calculate tool
- `/weather <location>` - Use the weather tool
- `/translate <text> to <language>` - Use the translate tool

## Configuration

You can customize the workflow through environment variables or by editing the plugin.yaml file:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `server_host` | Host address to bind the server to | "0.0.0.0" |
| `server_port` | Port for the MCP server | 8042 |
| `llm_provider` | LLM provider to use | "openai" |
| `llm_model` | LLM model to use | "gpt-3.5-turbo" |
| `openai_api_key` | OpenAI API key | Environment variable |

## Tool Usage Patterns

The tools follow these request patterns:

- **Calculate**: `calculate: 2 + 2`
- **Weather**: `get_weather: London`
- **Translate**: `translate: Hello world to es`

## Extending the Demo

To add new tools to the demo:

1. Create a new handler method similar to the existing ones
2. Register it with the server in the `_register_server_tools` method
3. Add client request handling in the `_run_demo_client` method

## Troubleshooting

If you encounter connection issues:

- Ensure no other service is using port 8042 (or change the port in configuration)
- Check that your OpenAI API key is valid if using real LLM services
- Increase the delay time between server start and client connection if needed 