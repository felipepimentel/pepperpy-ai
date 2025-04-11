# Research Assistant Workflow

## Overview

The Research Assistant workflow is a PepperPy workflow plugin that automates the research process, from finding information to generating comprehensive reports. It demonstrates the capabilities of the PepperPy framework for creating complex, multi-step AI workflows.

## Key Features

- **Automated Research**: Find relevant information on any topic
- **Content Analysis**: Extract key points and concepts from multiple sources
- **Report Generation**: Create well-structured reports in various formats
- **Quality Review**: Automatically review and provide suggestions for improvement
- **Flexible Configuration**: Customize research depth, report format, and more

## Usage

### Direct Usage

For development and testing, you can use the workflow directly:

```python
from plugins.workflow.research_assistant.provider import ResearchAssistantAdapter

async def run_research():
    # Create and initialize the adapter
    adapter = ResearchAssistantAdapter(
        model_id="gpt-4",
        max_sources=5,
        report_format="markdown"
    )
    await adapter.initialize()
    
    try:
        # Execute research task
        result = await adapter.execute({
            "task": "research",
            "topic": "artificial intelligence"
        })
        
        # Print research report
        if result["status"] == "success":
            print(f"Research ID: {result['research_id']}")
            
            # Get complete result with report content
            complete = await adapter.execute({
                "task": "get_result",
                "research_id": result["research_id"]
            })
            
            if complete["status"] == "success":
                print(complete["research"]["report"])
    finally:
        # Clean up resources
        await adapter.cleanup()
```

### Command Line Demo

A simple command-line demo is included:

```bash
# Basic usage
python plugins/workflow/research_assistant/run_research_demo.py "Artificial Intelligence"

# Specify format and max sources
python plugins/workflow/research_assistant/run_research_demo.py "Machine Learning" --format html --max-sources 3
```

## Workflow Configuration

The workflow accepts the following configuration options:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| model_id | string | LLM model to use | gpt-3.5-turbo |
| research_depth | string | Depth of research (basic, standard, comprehensive) | standard |
| max_sources | integer | Maximum number of sources to retrieve | 5 |
| report_format | string | Format of the report (markdown, html, text) | markdown |
| include_critique | boolean | Whether to include review feedback | true |

## Tasks

The workflow supports the following tasks:

### 1. Research

```python
result = await adapter.execute({
    "task": "research",
    "topic": "artificial intelligence",
    "max_sources": 5,  # optional
    "report_format": "markdown",  # optional
    "include_critique": True  # optional
})
```

Returns:
```json
{
    "status": "success",
    "research_id": "unique-research-id",
    "topic": "artificial intelligence",
    "sources_count": 5,
    "report_length": 1542,
    "duration_seconds": 6.5,
    "has_review": true
}
```

### 2. Get Result

```python
result = await adapter.execute({
    "task": "get_result",
    "research_id": "unique-research-id"
})
```

Returns the complete research result including the report content and all analysis.

### 3. Status

```python
result = await adapter.execute({
    "task": "status"
})
```

Returns the current workflow status including configuration and any active research.

## Implementation Details

This workflow demonstrates several core PepperPy capabilities:

1. **Workflow Orchestration**: Coordinating multi-step processes
2. **Resource Management**: Proper initialization and cleanup
3. **Error Handling**: Graceful error handling with detailed feedback
4. **Configurability**: Flexible parameter handling

## Demo Implementation Note

The current implementation uses simulated responses for demonstration purposes. In a real-world implementation, this would integrate with:

- LLM providers for analysis and report generation
- Search APIs for information retrieval
- Vector databases for relevant content lookup
- Document processing for analyzing retrieved content 