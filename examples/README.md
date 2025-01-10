# PepperPy AI Examples

This directory contains examples demonstrating the AI functionality of PepperPy.

## Basic Examples

- `basic_chat.py`: Demonstrates basic chat completion functionality
- `streaming.py`: Shows how to use streaming responses
- `teams/advanced_team.py`: Demonstrates advanced team functionality
- `teams/autogen_team.py`: Shows how to use AutoGen teams

## Running Examples

Each example can be run directly:

```bash
# Run basic chat example
python -m examples.basic_chat

# Run streaming example
python -m examples.streaming

# Run team examples
python -m examples.teams.advanced_team
python -m examples.teams.autogen_team
```

## Requirements

All examples require pepperpy-ai to be installed:

```bash
pip install pepperpy-ai
```

## Environment Variables

Some examples require environment variables to be set:

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=your-api-key
```
