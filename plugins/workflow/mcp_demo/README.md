# MCP Demo Workflow

## Overview

This workflow demonstrates the complete integration of Model Context Protocol (MCP) server and client with agent orchestration capabilities. It provides a unified interface for:

1. Running an MCP server with registered tools
2. Connecting a client to the server
3. Coordinating multiple agents to perform complex tasks

## Features

- **MCP Server**: Hosts LLM models and tools
- **MCP Client**: Connects to the server and uses its capabilities
- **Agent Orchestration**: Coordinates multiple agents to perform complex tasks
- **Built-in Tools**: Calculate, weather, translate, and more
- **Extensible**: Easy to add new agents and tools

## Architecture

The MCP demo consists of these main components:

```
┌──────────────────┐       ┌──────────────────┐
│                  │       │                  │
│    MCP Server    │◄──────┤   MCP Client     │
│                  │       │                  │
└────────┬─────────┘       └──────────────────┘
         │
         │
         ▼
┌────────────────────────────────────────┐
│                                        │
│          Agent Orchestrator            │
│                                        │
│  ┌─────────┐   ┌─────────┐  ┌────────┐ │
│  │         │   │         │  │        │ │
│  │ Planner │──►│Executor │─►│ Critic │ │
│  │         │   │         │  │        │ │
│  └─────────┘   └─────────┘  └────────┘ │
│                                        │
└────────────────────────────────────────┘
```

## Quick Start

### Running the Server

```bash
# Start the MCP server
python mcp.py server

# With custom host and port
python mcp.py server --host 127.0.0.1 --port 9000
```

### Connecting a Client

```bash
# Connect to the local server
python mcp.py client

# Connect to a remote server
python mcp.py client --host api.example.com --port 443
```

### Using Agent Orchestration

```bash
# Run an agent workflow for a specific task
python mcp.py agent "Create a marketing plan for a new eco-friendly product"

# With custom agent sequence
python mcp.py agent "Research top 5 competitors" --workflow "planner,executor"
```

### Using the Full Workflow

```bash
# Run the complete workflow
python mcp.py workflow

# With custom duration
python mcp.py workflow --duration 120
```

## Agent Orchestration

The agent orchestration layer coordinates multiple specialized agents to perform complex tasks.

### Default Agents

- **Planner**: Decomposes complex tasks into smaller steps (uses gpt-4)
- **Executor**: Executes individual tasks using available tools (uses gpt-3.5-turbo)
- **Critic**: Reviews outputs and suggests improvements (uses gpt-3.5-turbo)

### Tool Registry

All agents have access to tools based on their permissions:

- **Planning Tools**: analyze_task, create_plan
- **Execution Tools**: calculate, get_weather, translate
- **Review Tools**: analyze_output, suggest_improvements

### Memory System

Agents maintain memory across interactions:

- Short-term memory for current conversation
- Tool execution history for tracking actions
- Key-value store for arbitrary data

## CLI Tool

A command-line interface is provided for direct interaction with the MCP server:

```bash
# Start the CLI
python cli.py
```

Available commands:

- `/help` - Show help information
- `/quit` or `/exit` - Exit the CLI
- `/clear` - Clear conversation history
- `/models` - List available models
- `/model <model_id>` - Switch to a different model
- `/calc <expression>` - Use the calculate tool
- `/weather <location>` - Use the weather tool
- `/translate <text> to <language>` - Use the translate tool

## Configuration

The workflow can be customized through the `plugin.yaml` file:

```yaml
host: "0.0.0.0"           # Host address
port: 8000                # Port number
provider_type: "http"     # MCP provider type
llm_provider: "openai"    # LLM provider
llm_model: "gpt-3.5-turbo" # Default LLM model
demo_duration: 60         # Duration in seconds
enable_agent_orchestration: true # Enable agent orchestration
planner_model: "gpt-4"    # Model for planning agent
executor_model: "gpt-3.5-turbo" # Model for execution agent
critic_model: "gpt-3.5-turbo" # Model for critic agent
```

## Running Through PepperPy CLI

```bash
# Basic usage
python -m pepperpy.cli workflow run workflow/mcp_demo

# With OpenAI API key
OPENAI_API_KEY=your_key_here python -m pepperpy.cli workflow run workflow/mcp_demo

# Run with agent orchestration
python -m pepperpy.cli workflow run workflow/mcp_demo --input '{
  "workflow_type": "agent",
  "task": "Create a report on renewable energy trends"
}'
```

## Example Output

When running an agent workflow, you'll get output like:

```json
{
  "status": "success",
  "workflow_type": "agent",
  "agents_used": ["planner", "executor", "critic"],
  "result": {
    "status": "success",
    "results": [
      {
        "status": "success",
        "agent": "planner",
        "response": "Step 1: Research current renewable energy trends\nStep 2: Analyze data\nStep 3: Create report structure",
        "tools_used": ["analyze_task", "create_plan"]
      },
      {
        "status": "success",
        "agent": "executor",
        "response": "Based on my research, the top 3 renewable energy trends are...",
        "tools_used": ["calculate", "search"]
      },
      {
        "status": "success",
        "agent": "critic",
        "response": "The report is comprehensive but could be improved by adding more recent statistics.",
        "tools_used": ["analyze_output", "suggest_improvements"]
      }
    ],
    "final_output": "The report is comprehensive but could be improved by adding more recent statistics."
  }
}
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