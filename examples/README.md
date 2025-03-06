# PepperPy Framework Examples

This directory contains example code demonstrating how to use the PepperPy framework for various use cases.

## Directory Structure

- `composition/`: Examples demonstrating the universal composition API
  - `standard_pipeline_example.py`: Shows how to create and use standard sequential pipelines
  - `parallel_pipeline_example.py`: Shows how to create and use parallel pipelines for improved performance

- `content_processing/`: Examples for content processing capabilities
  - *Coming soon*

- `conversational/`: Examples for conversational AI capabilities
  - *Coming soon*

- `intent/`: Examples for intent recognition and processing
  - `intent_recognition_example.py`: Shows how to recognize, process, and classify intents

- `workflows/`: Examples for workflow definition and execution
  - `simple_workflow_example.py`: Shows how to create and execute a workflow with multiple steps

## Running the Examples

Most examples can be run directly using Python:

```bash
# Make sure you're in the project root directory
cd /path/to/pepperpy

# Run a specific example
python examples/composition/standard_pipeline_example.py
```

## Notes

- These examples are designed to demonstrate the API usage and may use mock implementations for some components.
- For production use, you should replace the mock implementations with real components.
- Some examples may require additional dependencies to be installed.

## Contributing

If you'd like to contribute additional examples, please follow these guidelines:

1. Create a new file in the appropriate subdirectory
2. Include comprehensive docstrings and comments
3. Make sure the example is self-contained and can be run independently
4. Update this README to include your new example 