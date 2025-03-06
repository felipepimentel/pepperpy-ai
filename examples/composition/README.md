# Composition Examples

This directory contains examples demonstrating how to use the universal composition API in the PepperPy framework.

## Available Examples

### Standard Pipeline Example

The `standard_pipeline_example.py` file demonstrates how to create and use a standard sequential pipeline for processing data. It shows:

- How to create custom source, processor, and output components
- How to compose these components into a pipeline
- How to execute the pipeline and handle the results

This example creates a pipeline that:
1. Fetches data from an RSS feed (simulated)
2. Processes the feed items to extract content
3. Outputs the results in JSON format

To run this example:

```bash
python examples/composition/standard_pipeline_example.py
```

### Parallel Pipeline Example

The `parallel_pipeline_example.py` file demonstrates how to create and use a parallel pipeline for improved performance when processing data. It shows:

- How to create a parallel pipeline using `compose_parallel`
- How to define components that can be executed in parallel
- How to compare performance between sequential and parallel execution

This example creates a pipeline that:
1. Fetches data from a web API (simulated)
2. Processes the data with multiple enrichment steps in parallel
3. Outputs the results in CSV format

The example also includes a comparison with sequential execution to demonstrate the performance benefits of parallel processing.

To run this example:

```bash
python examples/composition/parallel_pipeline_example.py
```

## Key Concepts

### Component Types

The composition API uses three main types of components:

- **Source Components**: Responsible for fetching data from external sources
- **Processor Components**: Transform or enrich the data
- **Output Components**: Format and output the processed data

### Pipeline Types

The framework supports two types of pipelines:

- **Standard Pipeline**: Executes components sequentially
- **Parallel Pipeline**: Executes processor components in parallel for improved performance

### Fluent API

The composition API uses a fluent interface for creating pipelines:

```python
pipeline = (
    compose("My Pipeline")
    .source(MySourceComponent(config))
    .process(MyProcessorComponent(config))
    .output(MyOutputComponent(config))
)

result = await pipeline.execute()
``` 