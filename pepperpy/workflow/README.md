# PepperPy Workflow System

The PepperPy Workflow System provides a unified framework for defining, building, and executing workflows within the PepperPy ecosystem. This system replaces previous fragmented implementations and offers a consistent API for all components.

## Key Components

### Base Components

- **WorkflowStep**: Represents a single step in a workflow with dependencies and metadata
- **WorkflowDefinition**: Defines the structure of a workflow, including steps and their relationships
- **BaseWorkflow**: Base implementation of a workflow with execution capabilities

### Builder API

- **WorkflowBuilder**: Fluent API for constructing workflow definitions
- **WorkflowStepBuilder**: Helper for building individual workflow steps

### Factory

- **WorkflowRegistry**: Registry for workflow implementations
- **WorkflowFactory**: Creates workflow instances from definitions
- **default_factory**: Global factory instance for convenience

## Usage Examples

### Creating a Simple Workflow

```python
from pepperpy.workflow import WorkflowBuilder, default_factory

# Create a workflow definition
builder = WorkflowBuilder("data_processing")

# Add steps
builder.add_step("fetch_data", "Fetch Data", "http_get", {"url": "https://example.com/data"})
builder.add_step("process_data", "Process Data", "transform", {"format": "json"})
builder.depends_on("fetch_data")
builder.add_step("store_data", "Store Data", "database_write", {"table": "processed_data"})
builder.depends_on("process_data")

# Build the workflow definition
definition = builder.build()

# Create a workflow instance
workflow = default_factory.create(definition)

# Execute the workflow
results = await workflow.execute({"api_key": "your_api_key"})
```

### Creating a Custom Workflow Implementation

```python
from pepperpy.workflow import BaseWorkflow, WorkflowDefinition, WorkflowStep

class CustomWorkflow(BaseWorkflow):
    """Custom workflow implementation."""

    async def _execute_step(self, step: WorkflowStep, context: dict) -> any:
        """Execute a single step with custom logic."""
        if step.action == "custom_action":
            # Implement custom action
            return {"result": "Custom action executed", "params": step.parameters}
        
        # Fall back to default implementation
        return await super()._execute_step(step, context)

# Register the custom workflow
from pepperpy.workflow import default_factory
default_factory.register_workflow("custom_workflow", CustomWorkflow)
```

### Loading a Workflow from a Dictionary

```python
workflow_data = {
    "name": "data_pipeline",
    "metadata": {
        "workflow_type": "data_processing",
        "version": "1.0"
    },
    "steps": {
        "step1": {
            "name": "Extract Data",
            "action": "extract",
            "parameters": {"source": "database"},
            "dependencies": []
        },
        "step2": {
            "name": "Transform Data",
            "action": "transform",
            "parameters": {"operations": ["filter", "map"]},
            "dependencies": ["step1"]
        },
        "step3": {
            "name": "Load Data",
            "action": "load",
            "parameters": {"destination": "warehouse"},
            "dependencies": ["step2"]
        }
    }
}

workflow = default_factory.create_from_dict(workflow_data)
results = await workflow.execute()
```

## Best Practices

1. **Use the Builder API** for constructing workflows programmatically
2. **Register custom workflow implementations** with the factory
3. **Validate workflow definitions** before execution
4. **Use metadata** to store additional information about workflows and steps
5. **Handle errors** appropriately during workflow execution

## Integration with Other PepperPy Components

The workflow system is designed to integrate seamlessly with other PepperPy components:

- **Audio Processing**: Define audio processing pipelines
- **Text Processing**: Create text transformation workflows
- **Data Analysis**: Build data analysis workflows
- **Model Training**: Define model training and evaluation workflows

## Migration from Legacy Implementations

If you're using the previous workflow implementations, migrate to the new unified system:

1. Replace imports from `workflows.definition` with `pepperpy.workflow`
2. Update workflow creation to use the new Builder API
3. Register custom workflow implementations with the factory
4. Update execution code to use the new async API 