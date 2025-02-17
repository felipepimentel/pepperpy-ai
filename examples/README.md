# Pepperpy Examples

This directory contains practical examples demonstrating how to use Pepperpy in real-world scenarios.

## Getting Started

1. Install dependencies:
```bash
poetry install
```

2. Set up your environment variables:
```bash
export PEPPERPY_API_KEY=your_api_key_here
```

## Example Structure

- `quickstart.py`: Basic introduction to Pepperpy's core concepts
- `use_cases/`: Real-world application examples
  - `personal_assistant.py`: Multi-feature personal assistant with task management, memory, and chat
  - `research_agent.py`: Automated research agent with search, analysis, and report generation
  - `collaborative_research.py`: Multi-agent system for collaborative research tasks

## Running Examples

Each example can be run using Poetry:

```bash
# Run quickstart example
poetry run python examples/quickstart.py

# Run personal assistant example
poetry run python examples/use_cases/personal_assistant.py

# Run research agent example
poetry run python examples/use_cases/research_agent.py

# Run collaborative research example
poetry run python examples/use_cases/collaborative_research.py
```

## Example Details

### Quickstart
Simple introduction to Pepperpy's core concepts including:
- Basic setup and configuration
- Resource management
- Error handling
- Cleanup and resource management

### Personal Assistant
Multi-feature personal assistant demonstrating:
- Task management
- Memory for context retention
- Chat interface
- Calendar integration
- Note-taking

### Research Agent
Single-agent research automation showing:
- Information search and collection
- Data analysis
- Report generation
- Memory management
- Progress monitoring

### Collaborative Research
Multi-agent research system featuring:
- Research Agent: Information gathering
- Analysis Agent: Data processing
- Writing Agent: Report generation
- Coordinator Agent: Workflow orchestration
- Inter-agent communication
- Shared memory management

## Best Practices

1. Always use proper error handling
2. Clean up resources when done
3. Use type hints for better code clarity
4. Follow the provided example structure for consistency
5. Include comprehensive logging for debugging

## Contributing

When adding new examples:
1. Focus on practical, real-world use cases
2. Include clear documentation and comments
3. Follow the existing code structure
4. Add the example to this README
5. Ensure all dependencies are in pyproject.toml 