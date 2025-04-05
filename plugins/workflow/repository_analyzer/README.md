# Repository Analyzer Workflow

A workflow plugin for analyzing code repositories and providing insights:

1. Code quality analysis
2. Repository structure analysis
3. Code complexity analysis
4. Dependency analysis
5. Security vulnerability scanning
6. Documentation coverage assessment

## Features

- Code Analysis: Analyze code quality, complexity, and structure
- Dependency Analysis: Identify and analyze dependencies
- Security Scanning: Check for security vulnerabilities
- Documentation Assessment: Evaluate documentation coverage 
- Integrated Insights: Generate reports with AI-powered recommendations

## Configuration

The workflow can be configured with these options:

- `repository_path`: Path to the repository to analyze (default: ".")
- `analysis_types`: Types of analysis to perform (default: ["code_quality", "structure", "complexity"])
- `include_patterns`: Glob patterns for files to include
- `exclude_patterns`: Glob patterns for files to exclude
- `max_files`: Maximum number of files to analyze (default: 1000)
- `llm_provider`: LLM provider to use for analysis (default: "openai")
- `llm_model`: LLM model to use for analysis (default: "gpt-4")
- `output_dir`: Directory to save results (default: "./output/repository_analysis")

## Usage

### Basic Repository Analysis

```python
from pepperpy.workflow import create_provider

# Create the repository analyzer workflow provider
workflow = create_provider("repository_analyzer", 
                         repository_path="./my_project",
                         analysis_types=["code_quality", "structure"])

# Run analysis
result = await workflow.execute({
    "task": "analyze_repository",
    "input": {
        "output_format": "markdown"
    }
})

# Print summary
print(result["summary"])
print(f"Analysis saved to: {result['output_path']}")
```

### Focused Analysis

```python
# Create workflow with focused analysis
workflow = create_provider("repository_analyzer", 
                         repository_path="./my_project",
                         include_patterns=["**/src/**/*.py"],
                         exclude_patterns=["**/tests/**"],
                         analysis_types=["complexity"])

# Run specific analysis
result = await workflow.execute({
    "task": "analyze_complexity",
    "input": {
        "metrics": ["cyclomatic", "cognitive"],
        "threshold": "medium"
    }
})

# Process results
issues = result["issues"]
print(f"Found {len(issues)} complexity issues")
for issue in issues:
    print(f"- {issue['file']}: {issue['description']}")
```

### Code Quality Analysis

```python
# Run code quality analysis
result = await workflow.execute({
    "task": "analyze_code_quality",
    "input": {
        "linter": "pylint",
        "min_score": 7.0
    }
})

# Process results
quality_report = result["report"]
print(f"Overall code quality score: {quality_report['overall_score']}")
print(f"Files analyzed: {quality_report['files_analyzed']}")
```

### Via CLI

```bash
# Run repository analysis via CLI
python -m pepperpy.cli workflow run workflow/repository_analyzer \
  --params "repository_path=./my_project" \
  --params "analysis_types=[code_quality,documentation]" \
  --params "task=analyze_repository" \
  --params "output_format=markdown"
```

## Requirements

- pydantic>=2.0.0
- jsonschema>=4.0.0
- radon>=5.1.0
- pylint>=2.17.0
- gitpython>=3.1.30

## Analysis Types

The workflow supports the following analysis types:

| Type | Description |
|------|-------------|
| code_quality | Analyzes code quality using linters and quality metrics |
| structure | Analyzes the repository structure and organization |
| complexity | Measures code complexity using metrics like cyclomatic complexity |
| dependencies | Analyzes project dependencies and their relationships |
| security | Scans for potential security vulnerabilities |
| documentation | Evaluates documentation coverage and quality |

You can configure which analyses to run using the `analysis_types` parameter. 