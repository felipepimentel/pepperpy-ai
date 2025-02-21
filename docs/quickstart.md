"""Quick Start Guide

This guide will help you get started with Pepperpy quickly.

## Basic Example

Here's a simple example that creates an agent and runs a task:

```python
import asyncio
from pepperpy.agents import BaseAgent
from pepperpy.agents.config import AgentConfig

async def main():
    # Create agent configuration
    config = AgentConfig(
        name="my-agent",
        description="My first Pepperpy agent",
    )

    # Create agent
    agent = BaseAgent(
        name="my-agent",
        version="0.1.0",
        config=config,
    )

    # Initialize agent
    await agent.initialize()

    # Run task
    result = await agent.run("Hello, world!")
    print(f"Result: {result}")

    # Clean up
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## Using Providers

Here's how to use different providers:

```python
from pepperpy.providers.llm import OpenAIProvider
from pepperpy.providers.memory import RedisProvider
from pepperpy.providers.storage import LocalStorageProvider

async def setup_providers():
    # Set up LLM provider
    llm = OpenAIProvider(
        api_key="your-api-key",
        model="gpt-4",
    )

    # Set up memory provider
    memory = RedisProvider(
        url="redis://localhost:6379",
        db=0,
    )

    # Set up storage provider
    storage = LocalStorageProvider(
        base_path="/path/to/storage",
    )

    # Initialize providers
    await llm.initialize()
    await memory.initialize()
    await storage.initialize()

    return llm, memory, storage
```

## Creating Workflows

Example of creating and running a workflow:

```python
from pepperpy.workflows import BaseWorkflow
from pepperpy.workflows.config import WorkflowConfig
from pepperpy.workflows.steps import Step

async def create_workflow():
    # Create workflow configuration
    config = WorkflowConfig(
        name="my-workflow",
        description="My first Pepperpy workflow",
    )

    # Create workflow steps
    steps = [
        Step(
            name="step-1",
            task="Process input",
            handler=lambda x: x.upper(),
        ),
        Step(
            name="step-2",
            task="Add greeting",
            handler=lambda x: f"Hello, {x}!",
        ),
    ]

    # Create workflow
    workflow = BaseWorkflow(
        name="my-workflow",
        version="0.1.0",
        config=config,
        steps=steps,
    )

    # Initialize workflow
    await workflow.initialize()

    # Run workflow
    result = await workflow.run("world")
    print(f"Result: {result}")  # Output: Hello, WORLD!

    # Clean up
    await workflow.cleanup()
```

## Using Events

Example of using the event system:

```python
from pepperpy.events import EventDispatcher
from pepperpy.events.handlers import EventHandler

class MyEventHandler(EventHandler):
    async def handle(self, event):
        print(f"Handling event: {event.type}")
        # Process event
        return {"status": "success"}

async def setup_events():
    # Create event dispatcher
    dispatcher = EventDispatcher()

    # Register event handler
    handler = MyEventHandler()
    dispatcher.register("my-event", handler)

    # Dispatch event
    event = {
        "type": "my-event",
        "data": {"message": "Hello!"},
    }
    result = await dispatcher.dispatch(event)
    print(f"Event result: {result}")
```

## Using Content Synthesis

Example of content synthesis:

```python
from pepperpy.content import BaseContent
from pepperpy.content.synthesis import BasicSynthesis

async def synthesize_content():
    # Create content sources
    sources = [
        "First piece of content",
        "Second piece of content",
        "Third piece of content",
    ]

    # Create synthesizer
    synthesizer = BasicSynthesis(
        name="basic-synthesis",
        version="0.1.0",
    )

    # Initialize synthesizer
    await synthesizer.initialize()

    # Synthesize content
    result = await synthesizer.synthesize(sources)
    print(f"Synthesized content: {result}")

    # Clean up
    await synthesizer.cleanup()
```

## Using the CLI

Example of using the CLI:

```bash
# Create an agent
pepperpy agent create my-agent --type assistant

# List agents
pepperpy agent list

# Deploy a workflow
pepperpy workflow deploy my-workflow.yaml

# Publish to hub
pepperpy hub publish my-component --visibility public

# Set configuration
pepperpy config set api.key your-api-key
```

## Next Steps

- Read the [Basic Concepts](./concepts.md) guide
- Explore the [User Guide](./user-guide/index.md)
- Check out the [API Reference](./api/index.md)
- Try the [Examples](./examples/index.md)""" 