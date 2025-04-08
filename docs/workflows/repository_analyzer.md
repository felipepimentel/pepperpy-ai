# Repository Analyzer Workflow

The Repository Analyzer is a PepperPy workflow that analyzes code repositories and provides insights about the codebase. This document explains how to use this workflow and its various capabilities.

## Basic Usage

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{"task": "analyze_repository", "repository_path": "."}'
```

## Tasks

The Repository Analyzer workflow supports the following tasks:

### 1. analyze_repository

Analyzes a repository and provides a general overview.

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{
  "task": "analyze_repository", 
  "repository_path": "/path/to/repository"
}'
```

#### Input Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| repository_path | string | Path to the repository to analyze | Yes |
| exclude_paths | array | Paths to exclude from analysis | No |
| max_files | integer | Maximum number of files to analyze | No |
| analysis_depth | string | Depth of analysis (basic, standard, deep) | No |

#### Output

The output is a JSON object with the following structure:

```json
{
  "title": "Repository Analysis",
  "type": "article",
  "content": "# Repository Analysis\n\n...",
  "references": [
    "https://example.com/reference1",
    "https://example.com/reference2"
  ],
  "refinements": [
    "grammar",
    "style",
    "clarity"
  ]
}
```

### 2. analyze_file

Analyzes a specific file in the repository.

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{
  "task": "analyze_file", 
  "repository_path": "/path/to/repository",
  "file_path": "src/main.py"
}'
```

#### Input Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| repository_path | string | Path to the repository | Yes |
| file_path | string | Path to the file to analyze (relative to repository) | Yes |
| analysis_type | string | Type of analysis (code, doc, security) | No |

#### Output

The output is a JSON object with detailed analysis of the specified file.

### 3. find_patterns

Searches for specific patterns or code smells in the repository.

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{
  "task": "find_patterns", 
  "repository_path": "/path/to/repository",
  "patterns": ["security_issue", "performance_bottleneck"]
}'
```

#### Input Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| repository_path | string | Path to the repository | Yes |
| patterns | array | List of patterns to search for | Yes |
| include_files | string | Glob pattern for files to include | No |
| exclude_files | string | Glob pattern for files to exclude | No |

#### Output

The output is a JSON object listing all instances of the requested patterns.

## Advanced Usage

### Custom Analysis Configuration

You can provide a custom configuration file for more advanced analysis:

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{
  "task": "analyze_repository", 
  "repository_path": ".",
  "config_path": "analysis_config.json"
}'
```

Where `analysis_config.json` might contain:

```json
{
  "analysis_modules": ["dependencies", "complexity", "security"],
  "thresholds": {
    "complexity": 10,
    "dependencies": 5,
    "security": "high"
  },
  "output_format": "markdown",
  "include_metrics": true
}
```

### Generating Reports

To generate a comprehensive report about the repository:

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{
  "task": "generate_report", 
  "repository_path": ".",
  "report_type": "full",
  "output_file": "report.md"
}'
```

This will create a detailed report in Markdown format.

## Integration with Other Workflows

The Repository Analyzer can be used in conjunction with other workflows:

### Content Generation

```bash
# First analyze the repository
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{
  "task": "analyze_repository", 
  "repository_path": ".",
  "output_file": "analysis.json"
}'

# Then generate documentation based on the analysis
python -m pepperpy.cli workflow run workflow/content_generator --input '{
  "task": "generate_documentation",
  "input_file": "analysis.json",
  "template": "project_readme"
}'
```

## Example Scripts

### Batch Analysis of Multiple Repositories

```python
import asyncio
import json
import os
from plugins.workflow.repository_analyzer.workflow import RepositoryAnalyzerWorkflow

async def analyze_repositories(repo_paths):
    """Analyze multiple repositories."""
    analyzer = RepositoryAnalyzerWorkflow()
    await analyzer.initialize()
    
    results = {}
    try:
        for path in repo_paths:
            repo_name = os.path.basename(path)
            print(f"Analyzing {repo_name}...")
            
            result = await analyzer.execute({
                "task": "analyze_repository",
                "repository_path": path,
                "analysis_depth": "standard"
            })
            
            results[repo_name] = result
            
        # Save combined results
        with open("analysis_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        print(f"Analysis complete. Results saved to analysis_results.json")
    finally:
        await analyzer.cleanup()

if __name__ == "__main__":
    repositories = [
        "/path/to/repo1",
        "/path/to/repo2",
        "/path/to/repo3"
    ]
    asyncio.run(analyze_repositories(repositories))
```

## Troubleshooting

### Common Issues

1. **Repository Path Not Found**

   Make sure the repository path is valid and accessible:
   
   ```bash
   # Check if the directory exists
   ls -la /path/to/repository
   ```

2. **Plugin Not Found**

   If you get a "Provider not found" error, make sure the plugin is correctly registered:
   
   ```bash
   # List available workflows
   python -m pepperpy.cli workflow list
   ```

3. **Analysis Timeout**

   For large repositories, you might encounter timeouts. Limit the scope of analysis:
   
   ```bash
   python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{
     "task": "analyze_repository", 
     "repository_path": ".",
     "max_files": 100,
     "analysis_depth": "basic"
   }'
   ```

## Contributing

We welcome contributions to improve the Repository Analyzer workflow. Here are some ideas:

1. Add support for new programming languages
2. Implement additional analysis patterns
3. Enhance report generation capabilities
4. Improve performance for large repositories

Please see the main [Contributing Guide](../contributing.md) for details on how to contribute. 