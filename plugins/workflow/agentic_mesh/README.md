# Agentic Mesh

A composable agent orchestration system for collaborative AI workflows.

## Overview

The Agentic Mesh is a workflow plugin for PepperPy that enables multiple specialized AI agents to collaborate on complex tasks. It provides a flexible, composable architecture for integrating various AI capabilities through a mesh network of agents with different roles and specializations.

Key features:
- **Multi-agent collaboration**: Orchestrate specialized agents for different aspects of complex workflows
- **Automatic routing**: Direct tasks to the most appropriate agent automatically
- **Dynamic configuration**: Add or remove agents at runtime
- **Knowledge sharing**: Common knowledge base accessible to all agents
- **Message-based communication**: Standardized communication protocol between agents

## Architecture

The Agentic Mesh implements a mesh network topology where:

1. **Agent Types**:
   - Analytical agents: Process and analyze data, extract insights
   - Decision agents: Make decisions based on analytical outputs
   - Conversion agents: Transform formats or translate between domains
   - Execution agents: Perform concrete actions based on decisions

2. **Core Components**:
   - Agent Registry: Manages agent registration and discovery
   - Knowledge Provider: Shared knowledge base for all agents
   - Communication Provider: Message routing between agents

3. **Communication Protocol**:
   - Standardized message types (task_request, response, notification, etc.)
   - Direct messaging between specific agents
   - Broadcast capabilities for mesh-wide communication

## Setup Requirements

To use the Agentic Mesh, you'll need the following providers:

1. **Agent Registry Provider**: Manages agent registration and discovery
2. **Knowledge Provider**: Provides shared knowledge storage
3. **Communication Provider**: Handles message routing
4. **Agent Providers**: One or more agent implementations

## Configuration

Example configuration in your `config.yaml`:

```yaml
workflow:
  agentic_mesh:
    workflow_name: "example_mesh"
    components:
      agent_registry: "agent/registry"
      knowledge_provider: "knowledge/vector_store"
      communication_provider: "communication/pubsub"
    agents:
      - agent_id: "analyzer"
        agent_type: "analytical"
        provider_type: "agent/llm_analyzer"
        parameters:
          model: "gpt-4"
      - agent_id: "decision_maker"
        agent_type: "decision"
        provider_type: "agent/llm_reasoning"
        parameters:
          model: "gpt-4"
      - agent_id: "executor"
        agent_type: "execution"
        provider_type: "agent/tool_executor"
        parameters:
          available_tools: ["web_search", "code_execution", "file_management"]
    default_routing:
      analysis: "analyzer"
      decision: "decision_maker"
      execution: "executor"
    log_level: "INFO"
```

## Usage Examples

### Basic Task Execution

```python
from pepperpy import PepperPy

async with PepperPy.create().with_workflow("agentic_mesh") as pp:
    result = await pp.workflow.execute({
        "action": "run_task",
        "task": "Analyze the performance of our web application",
        "parameters": {
            "task_type": "analysis"
        }
    })
    
    print(f"Task status: {result['status']}")
    print(f"Task result: {result['result']}")
```

### Agent Communication

```python
from pepperpy import PepperPy

async with PepperPy.create().with_workflow("agentic_mesh") as pp:
    # Send a direct message to a specific agent
    result = await pp.workflow.execute({
        "action": "direct_message",
        "target_agent": "analyzer",
        "message": {
            "type": "task_request",
            "content": "Please analyze this dataset and provide insights"
        }
    })
    
    # Broadcast a message to all agents
    result = await pp.workflow.execute({
        "action": "broadcast_message",
        "message": {
            "type": "notification",
            "content": "New data available for processing"
        }
    })
```

### Adding a New Agent at Runtime

```python
from pepperpy import PepperPy

async with PepperPy.create().with_workflow("agentic_mesh") as pp:
    # Add a new agent to the mesh
    result = await pp.workflow.execute({
        "action": "add_agent",
        "parameters": {
            "agent_id": "translator",
            "agent_type": "conversion",
            "provider_type": "agent/language_translator",
            "parameters": {
                "supported_languages": ["en", "es", "fr", "de"]
            }
        }
    })
    
    print(f"Agent added: {result['result']['message']}")
```

### Getting Mesh Status

```python
from pepperpy import PepperPy

async with PepperPy.create().with_workflow("agentic_mesh") as pp:
    # Get basic status
    basic_status = await pp.workflow.execute({
        "action": "status"
    })
    
    # Get detailed status including agent information
    detailed_status = await pp.workflow.execute({
        "action": "status",
        "detailed": True
    })
    
    print(f"Active agents: {detailed_status['result']['agent_count']}")
    print(f"Active tasks: {detailed_status['result']['active_tasks']}")
```

## CLI Usage

You can also interact with the Agentic Mesh directly through the CLI:

```bash
# Run a task
python -m pepperpy.cli workflow run workflow/agentic_mesh --input '{"action": "run_task", "task": "Analyze this text", "parameters": {"task_type": "analysis"}}'

# Get status
python -m pepperpy.cli workflow run workflow/agentic_mesh --input '{"action": "status", "detailed": true}'
```

## Extension Points

The Agentic Mesh can be extended in several ways:

1. **Custom Agent Types**: Define new agent types for specialized domains
2. **Custom Routing Rules**: Implement domain-specific routing logic
3. **Enhanced Knowledge Providers**: Integrate different vector stores or knowledge bases
4. **Communication Patterns**: Add new message types and communication protocols

## Development Roadmap

- [ ] Agent capability discovery
- [ ] Task planning and decomposition
- [ ] Improved inter-agent learning
- [ ] Feedback loops for self-improvement
- [ ] Visualization tools for mesh topology
- [ ] Performance monitoring and optimization 