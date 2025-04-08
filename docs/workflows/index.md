# PepperPy Workflows

This directory contains documentation for all available PepperPy workflows.

## Available Workflows

- [Repository Analyzer](repository_analyzer.md) - Analyzes code repositories and provides insights
- [Content Generator](content_generator.md) - Generates content based on prompts and templates
- [Text Processing](text_processing.md) - Processes and transforms text data
- [Intelligent Agents](intelligent_agents.md) - Orchestrates autonomous AI agents

## Getting Started

For general information on using workflows, see the [main README](../../README.md#pepperpy-workflows).

## Creating Custom Workflows

To create your own workflow, see the [Custom Workflow Guide](../development/custom_workflow.md).

## Common Patterns

Workflows in PepperPy follow these patterns:

1. **Task-Based Execution**: Each workflow supports multiple tasks through the `task` parameter
2. **Resource Management**: All workflows implement `initialize()` and `cleanup()` methods
3. **Configuration Options**: Workflows accept configuration through the `--config` parameter
4. **Direct Adapter Pattern**: Workflows can be used directly in Python code for testing and debugging

## Contributing

We welcome contributions of new workflows. Please see the [Contributing Guide](../contributing.md) for more information. 