# Pepperpy

A Python library for building AI-powered research assistants.

## 🚀 Quick Win (30 seconds)
```bash
# Install Pepperpy
pip install pepperpy

# Start interactive setup
pepperpy init

# Ask your first question
pepperpy test "What is AI?"
```

That's it! You're ready to use Pepperpy's powerful features:
```python
from pepperpy import Pepperpy

async def main():
    # Auto-configuration (or use Pepperpy.quick_start() for interactive setup)
    pepper = await Pepperpy.create()
    
    # Simple question
    result = await pepper.ask("What is AI?")
    print(result)
    
    # Interactive chat
    await pepper.chat("Tell me about AI")  # With initial message
    # Or just:
    await pepper.chat()  # Start blank chat

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

## Quick Start

```python
from pepperpy import Pepperpy

# Quick setup with interactive wizard
pepper = Pepperpy.quick_start()

# Or configure programmatically
async with await Pepperpy.create(api_key="your-key") as pepper:
    # Ask simple questions
    result = await pepper.ask("What is AI?")
    print(result)
    
    # Research topics in depth
    result = await pepper.research("Impact of AI in Healthcare")
    print(result.tldr)  # Short summary
    print(result.full)  # Full report
    print(result.bullets)  # Key points
    print(result.references)  # Sources
    
    # Use pre-configured teams
    team = await pepper.hub.team("research-team")
    async with team.run("Analyze AI trends") as session:
        print(f"Current step: {session.current_step}")
        print(f"Progress: {session.progress * 100:.0f}%")
```

## Features

- 🚀 Zero-config setup with smart defaults
- 🤖 Pre-configured agents and teams
- 📚 Built-in research capabilities
- 🔄 Flexible workflows
- 🎯 Progress monitoring
- 🔌 Easy integration

## Installation

```bash
pip install pepperpy
```

## Documentation

### Basic Usage

The simplest way to get started is with the interactive setup:

```bash
# Run interactive setup
$ pepperpy init

# Test it out
$ pepperpy test "What is AI?"
```

Or in your code:

```python
from pepperpy import Pepperpy

# Auto-configuration
pepper = await Pepperpy.create()

# With custom settings
pepper = await Pepperpy.create(
    api_key="your-key",
    model="openai/gpt-4"
)
```

### Research Assistant

```python
# Simple research
result = await pepper.research("Quantum Computing")
print(result.tldr)  # Short summary
print(result.full)  # Full report

# With custom parameters
result = await pepper.research(
    topic="Quantum Computing",
    depth="academic",
    max_sources=10
)
```

### Teams & Workflows

```python
# Use a pre-configured team
team = await pepper.hub.team("research-team")
async with team.run("Analyze AI trends") as session:
    # Monitor progress
    print(f"Step: {session.current_step}")
    print(f"Progress: {session.progress * 100:.0f}%")
    
    # Provide input if needed
    if session.needs_input:
        value = input(f"{session.input_prompt}: ")
        session.provide_input(value)
```

### Custom Agents

```python
# Create a custom agent
agent = await pepper.hub.create_agent(
    name="custom-researcher",
    base="researcher",  # Inherit from base agent
    config={
        "style": "technical",
        "depth": "deep"
    }
)

# Use the agent
result = await agent.research("Topic")

# Share with others
await pepper.hub.publish("custom-researcher")
```

## Examples

Check out the `examples/` directory for more usage examples:

- `quick_start.py`: Basic usage with interactive setup
- `research_workflow.py`: Advanced research workflow
- `custom_agent.py`: Creating custom agents
- `team_collaboration.py`: Using teams and workflows

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
