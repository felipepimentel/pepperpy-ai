# Repository Analysis Workflow

This workflow plugin provides comprehensive code repository analysis capabilities for the PepperPy framework.

## Features

- **Repository Structure Analysis**: Analyze file organization and directory structure
- **Code Quality Metrics**: Calculate complexity, lines of code, and other quality metrics
- **Customizable Reports**: Generate reports in different formats (Markdown, JSON, or plain text)
- **Component Analysis**: Focus analysis on specific components or directories

## Installation

Ensure you have the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Repository Analysis

```python
from pepperpy.workflow import create_provider

# Create the repo analysis workflow provider
workflow = create_provider("repo_analysis", max_files=200)

# Analyze a repository
result = await workflow.execute({
    "task": "analyze_repo",
    "input": {"repo_path": "/path/to/repo"}
})

# Print the summary
print(result["summary"])
```

### Component Analysis

```python
# Create the workflow with custom configuration
workflow = create_provider("repo_analysis", 
                         analysis_depth="detailed",
                         summary_format="markdown")

# Analyze a specific component
result = await workflow.execute({
    "task": "analyze_component",
    "input": {
        "repo_path": "/path/to/repo",
        "component_path": "src/core"
    }
})

# Access analysis results
structure = result["structure"]
metrics = result["metrics"]
summary = result["summary"]
```

### Custom Analysis Configuration

```python
# Create workflow with custom file patterns
workflow = create_provider("repo_analysis", 
                         include_patterns=["**/*.py", "**/*.ts"],
                         exclude_patterns=["**/tests/**", "**/node_modules/**"])

# Execute analysis
result = await workflow.execute({
    "task": "analyze_repo",
    "input": {"repo_path": "/path/to/repo"},
    "options": {
        "max_files": 500,
        "analysis_depth": "detailed"
    }
})

# Save the report to a file
with open("repo_analysis.md", "w") as f:
    f.write(result["report"])
```

## Configuration Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `max_files` | int | Maximum number of files to analyze | 100 |
| `analysis_depth` | str | Depth of analysis to perform | "standard" |
| `include_patterns` | list[str] | Glob patterns for files to include | ["**/*.py", "**/*.js"] |
| `exclude_patterns` | list[str] | Glob patterns for files to exclude | ["**/node_modules/**", "**/.git/**", "**/__pycache__/**"] |
| `include_metrics` | bool | Whether to include code quality metrics | True |
| `summary_format` | str | Format for the summary output | "markdown" |

## Output

The workflow analysis results contain the following information:

- `structure`: Repository structure information (file types, directory structure)
- `metrics`: Code quality metrics (complexity, LOC, etc.)
- `summary`: Concise summary of analysis results
- `report`: Detailed report with file-level metrics
- `success`: Whether the analysis was successful
- `message`: Status message
- `metadata`: Additional metadata about the analysis

## Standalone Usage

You can also use the plugin directly without the PepperPy framework:

```python
from plugins.workflow.repo_analysis.plugin import RepoAnalysisPlugin

# Create plugin instance
plugin = RepoAnalysisPlugin(
    max_files=100,
    include_patterns=["**/*.py", "**/*.js", "**/*.md"],
    exclude_patterns=["**/node_modules/**", "**/.git/**", "**/__pycache__/**"],
    summary_format="markdown"
)

# Initialize plugin
await plugin.initialize()

# Analyze repository
result = await plugin.analyze_repo("/path/to/repo")

# Print results
print(result["summary"])

# Clean up
await plugin.cleanup()
``` 