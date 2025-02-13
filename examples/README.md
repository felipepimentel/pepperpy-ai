# PepperPy Examples

This directory contains example scripts demonstrating various features of PepperPy.

## Running the Examples

All examples use Poetry for dependency management. Make sure you have Poetry installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Then install the dependencies:

```bash
poetry install
```

### Component Sharing Example

The `sharing_example.py` script demonstrates how to:
- Create and publish custom components (agents, workflows, teams)
- List available shared components
- Get detailed component information
- Use shared components in your code

To run the example:

```bash
poetry run python examples/sharing_example.py
```

The example will:
1. Create a custom researcher agent
2. Publish it to make it available for sharing
3. List all available shared components
4. Show detailed information about the shared agent
5. Use the shared agent to perform research

### Expected Output

The example will print:
- Research results from the custom agent
- A confirmation message when the agent is published
- A list of all shared components with their metadata
- Detailed information about the custom researcher agent
- Research results from using the shared agent

### Modifying the Example

You can modify the example to:
- Create and share different types of agents
- Create and share workflows
- Create and share teams
- Use different capabilities and configurations
- Change the research topics

See the inline comments in `sharing_example.py` for more details. 