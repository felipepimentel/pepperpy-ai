# PepperPy Workflow Module

This module provides workflow implementations for common tasks in PepperPy.

## Available Workflows

### A2A Workflow

The A2A workflow provides a reusable pipeline for agent-to-agent communication using the A2A protocol. It simplifies the setup and configuration of agents and enables easier communication between them.

#### Using the A2A Workflow

```python
import asyncio
from pepperpy.workflow import create_a2a_workflow, A2AWorkflowProvider
from pepperpy.a2a import create_provider as create_a2a_provider
from pepperpy.workflow.base import PipelineContext

async def use_a2a_workflow():
    # Create and initialize an A2A provider
    a2a_provider = await create_a2a_provider("mock") 
    await a2a_provider.initialize()
    
    try:
        # Use individual pipeline stages
        pipeline = create_a2a_workflow()
        context = PipelineContext()
        context.set("provider", a2a_provider)
        
        # Set up an agent
        agent_config = {
            "name": "PepperPy Agent",
            "description": "An agent for A2A communication",
            "endpoint": "http://localhost:8080/api/a2a",
            "capabilities": ["text-generation"],
        }
        
        # Run the entire pipeline
        task = pipeline.process(agent_config, context)
        
        # Alternatively, use the workflow provider directly
        workflow = A2AWorkflowProvider(provider_type="mock")
        await workflow.initialize()
        
        try:
            # Send a message to another agent
            result = await workflow.execute({
                "operation": "send_message",
                "target_agent_id": "other-agent-id",
                "message": "Hello from PepperPy!"
            })
        finally:
            await workflow.cleanup()
    finally:
        await a2a_provider.cleanup()

# Run the workflow
asyncio.run(use_a2a_workflow())
```

## Creating Custom Workflows

You can create custom workflows by:

1. Creating pipeline stages that inherit from `PipelineStage`
2. Creating a workflow provider that inherits from `WorkflowProvider`
3. Registering your workflow using `register_pipeline`

See `a2a_workflow.py` for a complete example of a workflow implementation. 