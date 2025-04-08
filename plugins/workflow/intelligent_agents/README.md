# Intelligent Agents Plugin

This plugin provides autonomous agent capabilities through the PepperPy framework. It enables the creation, configuration, and execution of AI agents that can perform complex tasks, interact with tools, and collaborate with other agents.

## Basic CLI Usage

```bash
# Run a single agent task
python -m pepperpy.cli workflow run workflow/intelligent_agents --input '{"task": "run_agent", "agent_type": "assistant", "prompt": "Research the latest advancements in quantum computing."}'
```

## Available Tasks

### Run Agent

Executes a single agent with the specified configuration.

```bash
python -m pepperpy.cli workflow run workflow/intelligent_agents --input '{
  "task": "run_agent", 
  "agent_type": "assistant",
  "prompt": "Research the latest advancements in quantum computing.",
  "max_iterations": 10,
  "tools": ["web_search", "document_retrieval"]
}'
```

**Parameters:**
- `agent_type` (string, required): Type of agent to run (assistant, researcher, executor, etc.)
- `prompt` (string, required): The task prompt for the agent
- `max_iterations` (integer, optional): Maximum number of iterations/steps
- `tools` (array, optional): List of tools the agent can use
- `memory` (boolean, optional): Enable agent memory of previous interactions
- `verbose` (boolean, optional): Enable detailed logging of agent actions

### Run Multi-Agent System

Executes a multi-agent system with collaborative agents.

```bash
python -m pepperpy.cli workflow run workflow/intelligent_agents --input '{
  "task": "run_multi_agent", 
  "agents": [
    {"name": "researcher", "type": "researcher", "tools": ["web_search"]},
    {"name": "writer", "type": "content_writer", "tools": ["text_editor"]},
    {"name": "critic", "type": "critic", "tools": []}
  ],
  "objective": "Create a comprehensive article about climate change.",
  "max_iterations": 20
}'
```

**Parameters:**
- `agents` (array, required): List of agent configurations
- `objective` (string, required): The overall objective for the multi-agent system
- `max_iterations` (integer, optional): Maximum number of iterations/steps
- `collaboration_type` (string, optional): How agents collaborate (sequential, parallel, hierarchical)
- `supervisor` (object, optional): Configuration for supervisor agent
- `timeout` (integer, optional): Maximum runtime in seconds

### Deploy Agent

Deploys an agent for long-running or scheduled tasks.

```bash
python -m pepperpy.cli workflow run workflow/intelligent_agents --input '{
  "task": "deploy_agent", 
  "agent_type": "monitor",
  "configuration": {
    "schedule": "0 * * * *",
    "prompt": "Monitor system metrics and alert if anomalies detected",
    "notification_method": "email"
  }
}'
```

**Parameters:**
- `agent_type` (string, required): Type of agent to deploy
- `configuration` (object, required): Agent-specific configuration
  - `schedule` (string, optional): Cron-style schedule for recurring tasks
  - `prompt` (string, required): The task prompt for the agent
  - `notification_method` (string, optional): How to notify about results/alerts
- `persistent` (boolean, optional): Whether the agent persists between runs
- `deployment_id` (string, optional): Custom identifier for the deployment

### Create Custom Agent

Creates a custom agent with specified capabilities.

```bash
python -m pepperpy.cli workflow run workflow/intelligent_agents --input '{
  "task": "create_custom_agent", 
  "name": "data_analyst",
  "capabilities": ["data_processing", "visualization", "statistical_analysis"],
  "tools": ["pandas", "matplotlib", "database_connector"],
  "description": "An agent that analyzes data and produces insightful reports",
  "save_to_library": true
}'
```

**Parameters:**
- `name` (string, required): Name for the custom agent
- `capabilities` (array, required): List of capabilities
- `tools` (array, required): List of tools the agent can use
- `description` (string, optional): Detailed description of the agent
- `base_agent` (string, optional): Base agent to extend
- `save_to_library` (boolean, optional): Whether to save the agent for future use

## Configuration

You can customize the agent execution with a configuration object:

```bash
python -m pepperpy.cli workflow run workflow/intelligent_agents \
  --input '{"task": "run_agent", "agent_type": "assistant", "prompt": "Research quantum computing"}' \
  --config '{
    "model": "gpt-4",
    "temperature": 0.3,
    "max_tokens": 4000,
    "logging_level": "debug",
    "tool_providers": {
      "web_search": "google",
      "text_editor": "basic"
    }
  }'
```

## Input Formats

The CLI supports different formats for providing input:

### JSON String
```bash
--input '{"task": "run_agent", "agent_type": "assistant", "prompt": "Research quantum computing"}'
```

### JSON File
```bash
--input path/to/input.json
```

### Command-line Parameters
```bash
--params task=run_agent agent_type=assistant prompt="Research quantum computing"
```

## Output Format

The output is a JSON object with the following structure:

```json
{
  "result": {
    "content": "# Quantum Computing Advancements\n\n...",
    "format": "markdown"
  },
  "agent_trace": [
    {"step": 1, "action": "web_search", "input": "latest quantum computing advancements", "output": "..."},
    {"step": 2, "action": "summarize", "input": "...", "output": "..."}
  ],
  "metadata": {
    "iterations": 8,
    "tools_used": ["web_search", "summarize"],
    "execution_time": "45.2s"
  }
}
```

## Save Results to File

Save agent results to a file:

```bash
python -m pepperpy.cli workflow run workflow/intelligent_agents \
  --input '{
    "task": "run_agent", 
    "agent_type": "assistant",
    "prompt": "Research quantum computing",
    "output_file": "research_report.md"
  }'
```

## Advanced Usage

### Agent with Tool Configuration

Configure specific tool behavior for an agent:

```bash
python -m pepperpy.cli workflow run workflow/intelligent_agents \
  --input '{
    "task": "run_agent", 
    "agent_type": "researcher",
    "prompt": "Research quantum computing",
    "tools": ["web_search", "document_retrieval", "summarizer"],
    "tool_config": {
      "web_search": {
        "search_engine": "google",
        "max_results": 5,
        "site_restrict": "research-papers"
      },
      "summarizer": {
        "style": "academic",
        "max_length": 500
      }
    }
  }'
```

### Agent with Memory

Run an agent with long-term memory:

```bash
python -m pepperpy.cli workflow run workflow/intelligent_agents \
  --input '{
    "task": "run_agent", 
    "agent_type": "assistant",
    "prompt": "Continue our previous discussion about quantum computing",
    "memory": true,
    "memory_id": "quantum_computing_research"
  }'
```

## Direct Usage in Python

For programmatic use or testing:

```python
import asyncio
from plugins.workflow.intelligent_agents.workflow import IntelligentAgentsWorkflow

async def run_agent():
    workflow = IntelligentAgentsWorkflow()
    await workflow.initialize()
    
    try:
        result = await workflow.execute({
            "task": "run_agent",
            "agent_type": "assistant",
            "prompt": "Research quantum computing",
            "max_iterations": 10,
            "tools": ["web_search", "document_retrieval"]
        })
        print(result["result"]["content"])
    finally:
        await workflow.cleanup()

if __name__ == "__main__":
    asyncio.run(run_agent())
```

## Troubleshooting

### Tool Access Issues

If an agent can't access required tools:

1. Check if the tool is correctly registered and available:
   ```bash
   python -m pepperpy.cli tool list
   ```

2. Make sure the tool is properly configured:
   ```bash
   python -m pepperpy.cli tool info tool_name
   ```

3. Check if the tool requires additional authentication or configuration.

### Agent Execution Timeouts

For complex agent tasks that time out:

1. Increase the maximum iterations or timeout:
   ```bash
   python -m pepperpy.cli workflow run workflow/intelligent_agents \
     --input '{
       "task": "run_agent", 
       "agent_type": "assistant",
       "prompt": "Research quantum computing",
       "max_iterations": 30,
       "timeout": 600
     }'
   ```

2. Break down the task into smaller subtasks.

### Provider Not Found

If you get a "Provider not found" error:

1. List available workflows to check registration:
   ```bash
   python -m pepperpy.cli workflow list
   ```

2. Ensure all dependencies for the intelligent_agents plugin are installed.

## Further Documentation

For more detailed documentation, see [docs/workflows/intelligent_agents.md](../../../docs/workflows/intelligent_agents.md). 