# Repository Analyzer Plugin

This plugin provides repository analysis capabilities through the PepperPy framework. It can analyze code repositories, individual files, and identify patterns in codebases.

## Basic CLI Usage

```bash
# Run a basic repository analysis
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{"task": "analyze_repository", "repository_path": "."}'
```

## Available Tasks

### Analyze Repository

Performs a comprehensive analysis of a code repository.

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{
  "task": "analyze_repository", 
  "repository_path": "/path/to/repository"
}'
```

**Parameters:**
- `repository_path` (string, required): Path to the repository
- `exclude_paths` (array, optional): Directories or files to exclude
- `max_files` (integer, optional): Maximum number of files to analyze
- `analysis_depth` (string, optional): Analysis depth (basic, standard, deep)

### Analyze File

Analyzes a specific file within a repository.

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{
  "task": "analyze_file", 
  "repository_path": "/path/to/repository",
  "file_path": "src/main.py"
}'
```

**Parameters:**
- `repository_path` (string, required): Path to the repository
- `file_path` (string, required): Path to the file (relative to repository)
- `analysis_type` (string, optional): Type of analysis (code, doc, security)

### Find Patterns

Searches for specific patterns or code smells in the repository.

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{
  "task": "find_patterns", 
  "repository_path": "/path/to/repository",
  "patterns": ["security_issue", "performance_bottleneck"]
}'
```

**Parameters:**
- `repository_path` (string, required): Path to the repository
- `patterns` (array, required): List of patterns to search for
- `include_files` (string, optional): Glob pattern for files to include
- `exclude_files` (string, optional): Glob pattern for files to exclude

## Configuration

You can customize the analysis with a configuration object:

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer \
  --input '{"task": "analyze_repository", "repository_path": "."}' \
  --config '{"model": "gpt-4", "max_tokens": 2000}'
```

## Input Formats

The CLI supports different formats for providing input:

### JSON String
```bash
--input '{"task": "analyze_repository", "repository_path": "."}'
```

### JSON File
```bash
--input path/to/input.json
```

### Command-line Parameters
```bash
--params task=analyze_repository repository_path=.
```

## Output Format

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

## Save Results to File

Save analysis results to a file:

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer \
  --input '{"task": "analyze_repository", "repository_path": ".", "output_file": "analysis.json"}'
```

## Advanced Usage

### Generate Report

Generate a comprehensive Markdown report:

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer \
  --input '{
    "task": "generate_report", 
    "repository_path": ".",
    "report_type": "full",
    "output_file": "report.md"
  }'
```

### Custom Analysis Configuration

Provide a custom configuration file for advanced analysis:

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer \
  --input '{
    "task": "analyze_repository", 
    "repository_path": ".",
    "config_path": "analysis_config.json"
  }'
```

## Direct Usage in Python

For programmatic use or testing:

```python
import asyncio
from plugins.workflow.repository_analyzer.workflow import RepositoryAnalyzerWorkflow

async def analyze_repo():
    analyzer = RepositoryAnalyzerWorkflow()
    await analyzer.initialize()
    
    try:
        result = await analyzer.execute({
            "task": "analyze_repository",
            "repository_path": "/path/to/repo",
            "analysis_depth": "standard"
        })
        print(result)
    finally:
        await analyzer.cleanup()

if __name__ == "__main__":
    asyncio.run(analyze_repo())
```

## Troubleshooting

### Provider Not Found

If you get a "Provider not found" error:

1. List available workflows to check registration:
   ```bash
   python -m pepperpy.cli workflow list
   ```

2. Verify the correct plugin structure:
   ```
   plugins/
   └── workflow/
       └── repository_analyzer/
           ├── plugin.yaml
           └── workflow.py
   ```

3. Check plugin.yaml has correct fields:
   ```yaml
   plugin_type: workflow
   provider_name: repository_analyzer
   ```

### Analysis Timeouts

For large repositories, limit the scope:

```bash
python -m pepperpy.cli workflow run workflow/repository_analyzer \
  --input '{
    "task": "analyze_repository", 
    "repository_path": ".",
    "max_files": 100,
    "analysis_depth": "basic"
  }'
```

## Further Documentation

For more detailed documentation, see [docs/workflows/repository_analyzer.md](../../../docs/workflows/repository_analyzer.md). 