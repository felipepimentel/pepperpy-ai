# PepperPy

A modern Python framework for AI applications with a focus on vertical domain integration.

## Architecture

PepperPy is organized into vertical domains, each with specific responsibilities:

| Domain       | Purpose                              | Status       |
|--------------|--------------------------------------|--------------|
| **LLM**      | Interaction with language models     | Implemented  |
| **RAG**      | Retrieval Augmented Generation       | Planned      |
| **Agent**    | Autonomous agents and assistants     | In Progress  |
| **Tool**     | Tools and external integrations      | Implemented  |
| **Cache**    | Caching strategies and storage       | Implemented  |
| **TTS**      | Text-to-speech operations            | Implemented  |
| **Discovery**| Service and component discovery      | Implemented  |

## Key Design Principles

1. **Vertical Domain Organization**: Each module represents a business domain, not a technical type
2. **Provider-Based Abstraction**: Domain-specific providers for various implementations
3. **Composable Interfaces**: Clean interfaces for building complex systems
4. **Configuration-Driven**: Configuration-first approach with minimal hard-coding

## Example Usage

```python
import asyncio
from pepperpy import PepperPy
from pepperpy.llm import Message

async def main():
    # Initialize with chosen providers
    pepper = PepperPy().with_llm("openai", api_key="your_key_here")
    
    # Initialize providers
    await pepper.initialize()
    
    # Chat with an LLM
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="What is PepperPy?")
    ]
    response = await pepper.llm.chat(messages)
    print(response)
    
    # Generate an embedding
    embedding = await pepper.llm.embed("This is a text to embed")
    
    # Use TTS
    audio_data = await pepper.tts.synthesize("Hello, world!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Project Status

The framework is currently in active development with several domains already implemented.

## Features

- **Provider-Based Architecture**: Easily swap implementations for each domain
- **Async-First Design**: Built for asynchronous operations from the ground up
- **Type-Safe Interfaces**: Strong typing throughout the codebase
- **Configuration Management**: Centralized configuration with provider-specific options
- **Consistent Error Handling**: Domain-specific error hierarchies
- **Extensible**: Create custom providers for any domain

## Installation

```bash
pip install pepperpy
```

## Available Providers

- **LLM**: OpenAI
- **TTS**: Azure TTS
- **Cache**: In-memory, Redis (planned)
- **Tool**: Local, Remote (planned)

## Storage Providers

PepperPy supports various storage backends for persistent data storage:

### SQLite Provider

The SQLite provider offers a lightweight, file-based storage solution that's perfect for development or small-scale applications.

```python
from pepperpy.storage.providers.sqlite import SQLiteProvider, SQLiteConfig

# Configure the SQLite provider
config = SQLiteConfig(
    database_path="./data/my_database.db",
    create_if_missing=True,
)

# Create the provider
provider = SQLiteProvider(config)

# Use the provider to store and retrieve data
async def store_data():
    # Connect to the database
    connection = await provider.get_connection()
    
    # Create a container
    container = StorageContainer(
        name="my_container",
        object_type=MyDataClass,
        description="My data container",
    )
    
    await provider.create_container(container)
    
    # Store an object
    obj = MyDataClass(id="obj1", name="Test Object")
    stored = await provider.put("my_container", obj)
    
    # Retrieve an object
    retrieved = await provider.get("my_container", "obj1")
```

For a complete example, see [examples/sqlite_storage_example.py](examples/sqlite_storage_example.py).

## Documentation

For detailed documentation and examples, see the [examples](./examples) directory.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Discovery and Plugins

PepperPy uses a layered discovery architecture:

1. **Discovery Module** - Provides low-level discovery interfaces
2. **Plugins Module** - Implements high-level plugin management

This separation allows clean architecture with proper separation of concerns. Discovery interfaces define the protocols for finding components, while the plugin system handles the complete lifecycle management.

### 7. Plugin Discovery

PepperPy includes a powerful plugin discovery system that makes it easy to find and use plugins:

```python
from pepperpy.plugin.providers.discovery.plugin_discovery import PluginDiscoveryProvider

discovery = PluginDiscoveryProvider(config={
    "scan_paths": ["path/to/plugins"]
})

await discovery.initialize()
plugins = await discovery.discover_plugins()
```

For more details, see [Discovery and Plugins Relationship](docs/architecture/discovery-plugins-relationship.md)

# PepperPy Workflows

PepperPy is a unified abstraction for AI/LLM ecosystems with a focus on agentic AI capabilities. This README focuses on the workflow system, which allows for the orchestration of complex AI-powered processes.

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/pepperpy.git
cd pepperpy

# Install dependencies
pip install -e .
```

### Using the CLI

PepperPy provides a command-line interface for working with workflows:

```bash
# List available workflows
python -m pepperpy.cli workflow list

# Get information about a specific workflow
python -m pepperpy.cli workflow info workflow/repository_analyzer

# Run a workflow
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{"task": "analyze_repository", "repository_path": "."}'
```

## Workflow Commands

### List Workflows

```bash
python -m pepperpy.cli workflow list
```

This command lists all available workflows in the system.

### Get Workflow Info

```bash
python -m pepperpy.cli workflow info workflow/NAME
```

This displays detailed information about a specific workflow, including:
- Description
- Version
- Configuration options
- Documentation
- Usage examples

### Run a Workflow

```bash
python -m pepperpy.cli workflow run workflow/NAME --input INPUT_DATA
```

Where:
- `NAME` is the name of the workflow to run
- `INPUT_DATA` is a JSON string or path to a JSON file containing input data

The input data format typically follows:

```json
{
  "task": "task_name",
  "repository_path": "/path/to/repository",
  "options": {
    "option1": "value1",
    "option2": "value2"
  }
}
```

## Input Data Options

Input data can be provided in several ways:

1. **JSON string**:
   ```bash
   --input '{"task": "analyze_repository", "repository_path": "."}'
   ```

2. **JSON file**:
   ```bash
   --input path/to/input.json
   ```

3. **Command-line parameters**:
   ```bash
   --params task=analyze_repository repository_path=.
   ```

## Configuration Options

Additional configuration for a workflow can be provided:

```bash
--config '{"model": "gpt-4", "api_key": "YOUR_API_KEY"}'
```

or using a configuration file:

```bash
--config path/to/config.json
```

## Creating Custom Workflows

### Workflow Plugin Structure

Workflows are implemented as plugins in the PepperPy plugin system. A typical workflow plugin has this structure:

```
plugins/
└── workflow/
    └── your_workflow/
        ├── plugin.yaml  # Plugin metadata
        └── workflow.py  # Workflow implementation
```

### Plugin.yaml Example

```yaml
name: your_workflow
version: 0.1.0
description: Description of your workflow
author: Your Name
plugin_type: workflow
provider_name: your_workflow
entry_point: workflow.YourWorkflowClass

# Configuration schema
config_schema:
  type: object
  properties:
    option1:
      type: string
      description: Description of option1
      default: default_value
    option2:
      type: boolean
      description: Description of option2
      default: false
```

### Workflow Implementation Example

```python
# workflow.py
from pepperpy.workflow.base import WorkflowProvider
from pepperpy.plugin import workflow

@workflow(
    name="your_workflow",
    description="Description of your workflow",
    version="0.1.0",
)
class YourWorkflowClass(WorkflowProvider):
    """Your workflow implementation."""
    
    def __init__(self, **kwargs):
        """Initialize the workflow."""
        super().__init__(**kwargs)
        self.option1 = kwargs.get("option1", "default_value")
        self.option2 = kwargs.get("option2", False)
        self.initialized = False
    
    async def initialize(self):
        """Initialize resources."""
        if self.initialized:
            return
        # Initialize resources
        self.initialized = True
    
    async def cleanup(self):
        """Clean up resources."""
        if not self.initialized:
            return
        # Clean up resources
        self.initialized = False
    
    async def execute(self, input_data):
        """Execute the workflow.
        
        Args:
            input_data: Dictionary with task and parameters
        
        Returns:
            Result dictionary
        """
        # Get task from input data
        task = input_data.get("task", "default_task")
        
        # Execute appropriate task
        if task == "task1":
            return await self._execute_task1(input_data)
        elif task == "task2":
            return await self._execute_task2(input_data)
        else:
            return {
                "status": "error", 
                "message": f"Unknown task: {task}"
            }
    
    async def _execute_task1(self, input_data):
        """Execute task1."""
        # Task implementation
        return {"status": "success", "result": "Task 1 completed"}
    
    async def _execute_task2(self, input_data):
        """Execute task2."""
        # Task implementation
        return {"status": "success", "result": "Task 2 completed"}
```

## Available Workflows

PepperPy comes with several built-in workflows:

### Repository Analyzer

Analyzes a code repository and provides insights.

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{"task": "analyze_repository", "repository_path": "."}'
```

### Content Generator

Generates content based on provided prompts and templates.

```bash
python -m pepperpy.cli workflow run workflow/content_generator --input '{"task": "generate_content", "prompt": "Write a blog post about AI"}'
```

### Text Processing

Processes and transforms text with various operations.

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{"task": "normalize", "text": "Text to normalize"}'
```

## Troubleshooting

### Plugin Registration Issues

If you encounter issues with workflow plugins not being found:

1. Make sure your workflow follows the correct directory structure:
   ```
   plugins/workflow/your_workflow/
   ```

2. Check that your plugin.yaml has the correct fields:
   ```yaml
   plugin_type: workflow
   provider_name: your_workflow
   ```

3. Verify that your workflow class is properly decorated:
   ```python
   @workflow(name="your_workflow", ...)
   class YourWorkflow(WorkflowProvider):
       ...
   ```

### Running Direct Adapter

For testing or debugging, you can use the direct adapter pattern:

```python
from plugins.workflow.your_workflow.workflow import YourWorkflowClass

async def run_direct():
    # Create adapter directly
    adapter = YourWorkflowClass()
    
    # Initialize
    await adapter.initialize()
    
    try:
        # Execute
        result = await adapter.execute({"task": "your_task"})
        print(result)
    finally:
        # Clean up
        await adapter.cleanup()

# Run the function
if __name__ == "__main__":
    import asyncio
    asyncio.run(run_direct())
```

## Contributing

We welcome contributions to PepperPy! Here are some ways you can help:

1. Report bugs and request features
2. Submit pull requests for bug fixes and features
3. Improve documentation and examples
4. Create new workflows for common tasks

Please follow the coding standards defined in the project.

## License

PepperPy is licensed under [LICENSE]. See the LICENSE file for details. 