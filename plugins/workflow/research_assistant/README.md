# Research Assistant Workflow

This PepperPy workflow plugin automates the process of conducting research on a topic, analyzing information, and generating comprehensive reports.

## Features

- **Information Gathering**: Finds relevant information on a topic using real search services
- **Content Analysis**: Analyzes content from multiple sources using LLM capabilities
- **Report Generation**: Creates professional research reports with key findings and insights
- **Report Review**: Optionally provides a critique with improvement suggestions

## Usage

### Basic Usage

```python
from pepperpy import PepperPy

# Initialize PepperPy with the research_assistant workflow
pepperpy = PepperPy.create().with_workflow("research_assistant").build()

# Execute research
result = await pepperpy.workflow.execute({
    "task": "research",
    "topic": "Artificial Intelligence Ethics"
})

# Get the research results
research_id = result["research_id"]
research_results = await pepperpy.workflow.execute({
    "task": "get_result",
    "research_id": research_id
})

# Print the report
print(research_results["research"]["report"])
```

### Direct Adapter Usage

For development or testing, you can use the adapter directly:

```python
from plugins.workflow.research_assistant.provider import ResearchAssistantAdapter

# Create and initialize the adapter
adapter = ResearchAssistantAdapter(
    model_id="gpt-4", 
    max_sources=5,
    api_key="your-api-key"
)
await adapter.initialize()

try:
    # Execute research
    result = await adapter.execute({
        "task": "research",
        "topic": "Climate Change Solutions"
    })
    
    # Get full research results
    if result["status"] == "success":
        research_id = result["research_id"]
        research_results = await adapter.execute({
            "task": "get_result",
            "research_id": research_id
        })
        print(research_results["research"]["report"])
finally:
    # Clean up resources
    await adapter.cleanup()
```

## CLI Demo

A command-line demo script is provided to showcase the workflow:

```bash
# Basic usage
python run_research_demo.py "Quantum Computing"

# Advanced options
python run_research_demo.py "Machine Learning Applications" --format markdown --max-sources 5 --model gpt-4 --api-key "your-api-key"
```

## Configuration

Configure the workflow through the PepperPy API or plugin.yaml:

| Option | Description | Default |
|--------|-------------|---------|
| `model_id` | LLM model to use | `gpt-3.5-turbo` |
| `research_depth` | Depth of research (basic, standard, comprehensive) | `standard` |
| `max_sources` | Maximum number of sources to retrieve | `5` |
| `report_format` | Format of the generated report (markdown, html, text) | `markdown` |
| `include_critique` | Whether to include a critique/review of the report | `true` |
| `api_key` | API key for services | Environment variable |

## Implementation Details

This workflow uses real services:

1. **LLM Integration**: Uses OpenAI or Anthropic models for content analysis and report generation
2. **Search Integration**: Connects to search providers to find relevant information
3. **Pipeline Approach**: Implements a multi-stage research pipeline
4. **Resource Management**: Properly handles resource initialization and cleanup
5. **Error Handling**: Provides robust error handling and fallback mechanisms

## Requirements

- PepperPy core framework
- Access to LLM API (OpenAI or Anthropic)
- Access to search API
- Python 3.10+

## Dependencies

- `pepperpy`: Core framework
- `asyncio`: For asynchronous operations

## Integration Examples

### Web Application

```python
from fastapi import FastAPI
from pepperpy import PepperPy

app = FastAPI()
pepperpy = PepperPy.create().with_workflow("research_assistant").build()

@app.post("/research")
async def research(topic: str):
    result = await pepperpy.workflow.execute({
        "task": "research",
        "topic": topic
    })
    return result
```

### Jupyter Notebook

```python
import asyncio
from pepperpy import PepperPy

# Initialize PepperPy
pepperpy = await PepperPy.create().with_workflow("research_assistant").build()

# Research a topic
topic = "Renewable Energy"
result = await pepperpy.workflow.execute({
    "task": "research",
    "topic": topic
})

# Display the research report
from IPython.display import Markdown
research_id = result["research_id"]
full_result = await pepperpy.workflow.execute({
    "task": "get_result", 
    "research_id": research_id
})
Markdown(full_result["research"]["report"])
``` 