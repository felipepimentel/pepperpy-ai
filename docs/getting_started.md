# Getting Started

## Installation

```bash
pip install pepperpy
```

## Quick Start (30 seconds)

The fastest way to get started with Pepperpy:

```bash
# Start interactive setup
pepperpy init

# Ask your first question
pepperpy test "What is AI?"
```

That's it! You're ready to use Pepperpy's powerful features.

## Basic Usage

### Simple Questions

```python
from pepperpy import Pepperpy

async def main():
    # Auto-configuration (or use Pepperpy.quick_start() for interactive setup)
    pepper = await Pepperpy.create()
    
    # Ask a simple question
    result = await pepper.ask("What is AI?")
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Interactive Chat

```python
async def chat_example():
    pepper = await Pepperpy.create()
    
    # Start chat with initial message
    await pepper.chat("Tell me about AI")
    
    # Or start a blank chat session
    await pepper.chat()
    
    # During chat:
    # - Press Ctrl+C to exit
    # - Type /help for commands
    # - Type /clear to clear history
    # - Type /save to save conversation
```

### Research Assistant

```python
async def research_example():
    pepper = await Pepperpy.create()
    
    # Simple research
    result = await pepper.research("Impact of AI in Healthcare")
    print(result.tldr)  # Quick summary
    print(result.full)  # Full report
    print(result.bullets)  # Key points
    print(result.references)  # Sources
    
    # With custom parameters
    result = await pepper.research(
        topic="Quantum Computing",
        depth="academic",  # basic, detailed, comprehensive
        style="technical",  # casual, business, academic
        format="report"  # summary, bullets, report
    )
```

### Team Collaboration

```python
async def team_example():
    pepper = await Pepperpy.create()
    
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

## Configuration

### Environment Variables

You can configure Pepperpy using environment variables:

```bash
# API Key (required)
PEPPERPY_API_KEY=your-api-key

# Model Selection (optional)
PEPPERPY_MODEL=openai/gpt-4  # Default model
PEPPERPY_TEMPERATURE=0.7     # Response creativity (0.0-1.0)
PEPPERPY_MAX_TOKENS=2048     # Maximum response length
```

### Programmatic Configuration

Or configure programmatically:

```python
pepper = await Pepperpy.create(
    api_key="your-api-key",
    model="openai/gpt-4",
    temperature=0.7,
    max_tokens=2048
)
```

### Interactive Setup

For guided setup with validation:

```python
pepper = await Pepperpy.quick_start()  # Launches setup wizard
```

## CLI Commands

Pepperpy comes with helpful CLI commands:

```bash
# Interactive setup
pepperpy init

# Quick test
pepperpy test "What is AI?"

# Run diagnostics
pepperpy doctor

# Start chat session
pepperpy chat

# Research a topic
pepperpy research "Impact of AI" --depth comprehensive --style academic
```

## Next Steps

1. Explore the [Core Concepts](core_concepts.md) guide
2. Check out the [API Reference](api_reference/index.md)
3. Browse [Example Projects](examples/) 