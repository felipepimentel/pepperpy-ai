# Integrating Multiple Plugins in PepperPy

This guide demonstrates how to combine multiple PepperPy plugins to create powerful, integrated workflows.

## Basic Multi-Plugin Integration

PepperPy's modular design allows plugins to work together seamlessly. Here's how to combine them using the CLI:

```bash
# First plugin in the chain
python -m pepperpy.cli workflow run workflow/repository_analyzer --input '{
  "task": "analyze_repository",
  "repository_path": "."
}' --output "repo_analysis.json"

# Second plugin using the output from the first
python -m pepperpy.cli workflow run workflow/content_generator --input '{
  "task": "generate_documentation",
  "source_data_file": "repo_analysis.json"
}'
```

## Using the Pipeline Plugin

For more complex multi-step workflows, you can use the pipeline plugin:

```bash
python -m pepperpy.cli workflow run workflow/pipeline --input '{
  "steps": [
    {
      "plugin": "repository_analyzer",
      "task": "analyze_repository",
      "params": {
        "repository_path": ".",
        "analysis_depth": "deep"
      }
    },
    {
      "plugin": "data_processing",
      "task": "transform_data",
      "params": {
        "operations": [
          {"type": "filter", "column": "complexity", "operator": ">", "value": 10}
        ]
      }
    },
    {
      "plugin": "content_generator",
      "task": "generate_refactoring_plan",
      "params": {
        "format": "markdown"
      }
    }
  ],
  "pass_results": true,
  "parallel_execution": false
}'
```

## Programmatic Integration in Python

For more control, combine plugins programmatically:

```python
import asyncio
from pepperpy.plugin.registry import PluginRegistry
from pepperpy.plugin.discovery import discover_plugins

async def complex_workflow():
    # Discover and register plugins
    await discover_plugins()
    registry = PluginRegistry()
    
    # Initialize plugins
    repo_analyzer = await registry.create_provider_instance("workflow", "repository_analyzer")
    text_processor = await registry.create_provider_instance("workflow", "text_processing")
    content_gen = await registry.create_provider_instance("workflow", "content_generator")
    
    try:
        # Step 1: Analyze the repository
        analysis_result = await repo_analyzer.execute({
            "task": "analyze_repository",
            "repository_path": ".",
            "analysis_depth": "deep"
        })
        
        # Step 2: Extract and process important sections
        repo_summary = analysis_result["summary"]
        processed_text = await text_processor.execute({
            "task": "summarize",
            "text": repo_summary,
            "max_length": 500
        })
        
        # Step 3: Generate documentation
        docs = await content_gen.execute({
            "task": "generate_documentation",
            "source_data": processed_text["processed_text"],
            "format": "markdown"
        })
        
        return docs
    finally:
        # Clean up resources
        await repo_analyzer.cleanup()
        await text_processor.cleanup()
        await content_gen.cleanup()

if __name__ == "__main__":
    result = asyncio.run(complex_workflow())
    print(result["content"])
```

## Common Integration Patterns

### Data Transformation Chain

Process data through multiple transformations:

1. Load data with local plugin
2. Process with data_processing plugin
3. Analyze with text_processing plugin
4. Visualize results

```bash
python -m pepperpy.cli workflow run workflow/pipeline --input '{
  "steps": [
    {
      "plugin": "local",
      "task": "read_file",
      "params": {"path": "data.csv"}
    },
    {
      "plugin": "data_processing",
      "task": "transform_data",
      "params": {
        "operations": [
          {"type": "filter", "column": "status", "operator": "==", "value": "active"}
        ]
      }
    },
    {
      "plugin": "text_processing",
      "task": "extract",
      "params": {"entities": ["date", "organization"]}
    },
    {
      "plugin": "data_processing",
      "task": "visualize_data",
      "params": {
        "visualizations": [{"type": "bar", "x": "organization", "y": "count"}],
        "output": "organization_counts.png"
      }
    }
  ]
}'
```

### Intelligent Agent with Tool Integration

Use the intelligent_agents plugin with other plugins as tools:

```bash
python -m pepperpy.cli workflow run workflow/intelligent_agents --input '{
  "task": "run_agent",
  "agent_type": "research_assistant",
  "prompt": "Analyze our codebase and suggest improvements",
  "tools": [
    {
      "name": "repository_analyzer",
      "plugin": "repository_analyzer",
      "tasks": ["analyze_repository", "find_patterns"]
    },
    {
      "name": "code_generator",
      "plugin": "content_generator",
      "tasks": ["generate_code", "refactor_code"]
    },
    {
      "name": "filesystem",
      "plugin": "local",
      "tasks": ["read_file", "write_file", "list_files"]
    }
  ],
  "max_iterations": 20
}'
```

## Custom Plugin Wrappers

You can create wrapper scripts for common multi-plugin workflows:

```python
#!/usr/bin/env python
# code_analyzer.py
import asyncio
import argparse
import json
from pepperpy.plugin.registry import PluginRegistry
from pepperpy.plugin.discovery import discover_plugins

async def analyze_and_improve(repo_path, output_file):
    await discover_plugins()
    registry = PluginRegistry()
    
    analyzer = await registry.create_provider_instance("workflow", "repository_analyzer")
    text_proc = await registry.create_provider_instance("workflow", "text_processing")
    content_gen = await registry.create_provider_instance("workflow", "content_generator")
    
    try:
        # Analyze repo
        analysis = await analyzer.execute({
            "task": "analyze_repository",
            "repository_path": repo_path
        })
        
        # Summarize findings
        summary = await text_proc.execute({
            "task": "summarize",
            "text": json.dumps(analysis["details"]),
            "max_length": 1000
        })
        
        # Generate improvement plan
        plan = await content_gen.execute({
            "task": "generate_refactoring_plan",
            "source_data": summary["processed_text"]
        })
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump({
                "analysis": analysis,
                "summary": summary["processed_text"],
                "improvement_plan": plan["content"]
            }, f, indent=2)
            
        print(f"Results saved to {output_file}")
    finally:
        await analyzer.cleanup()
        await text_proc.cleanup()
        await content_gen.cleanup()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze code and suggest improvements")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument("--output", default="code_analysis.json", help="Output file")
    args = parser.parse_args()
    
    asyncio.run(analyze_and_improve(args.repo_path, args.output))
```

## Troubleshooting Multi-Plugin Integration

### Data Compatibility Issues

Ensure data formats are compatible between plugins:

1. Use the `data_processing` plugin to transform data formats if needed:
   ```bash
   python -m pepperpy.cli workflow run workflow/data_processing --input '{
     "task": "transform_data",
     "source": "input.json",
     "operations": [
       {"type": "convert", "format": "csv"}
     ],
     "output": "transformed.csv"
   }'
   ```

2. Set `output_format` explicitly when using multiple plugins.

### Plugin Dependencies

Some integrations may require specific dependencies:

1. Ensure all required plugins are registered:
   ```bash
   python -m pepperpy.cli workflow list
   ```

2. Check plugin-specific dependencies:
   ```bash
   python -m pepperpy.cli workflow info workflow/data_processing
   ```

### Error Handling in Pipelines

Handle errors gracefully in multi-plugin workflows:

```python
try:
    # Attempt to run the first plugin
    result1 = await plugin1.execute(params)
except Exception as e:
    # Fall back to alternative approach
    print(f"Error in first plugin: {e}")
    result1 = {"default": "data"}
    
# Continue with next plugin using result1 or fallback data
```

## Advanced Integration Examples

### Collaborative Research Assistant

Combine repository analysis, web research, and content generation:

```bash
python -m pepperpy.cli workflow run workflow/pipeline --input '{
  "steps": [
    {
      "plugin": "repository_analyzer",
      "task": "analyze_repository",
      "params": {"repository_path": "."}
    },
    {
      "plugin": "intelligent_agents",
      "task": "run_agent",
      "params": {
        "agent_type": "researcher",
        "prompt": "Research best practices related to the technologies in this codebase",
        "tools": ["web_search"]
      }
    },
    {
      "plugin": "content_generator",
      "task": "generate_documentation",
      "params": {
        "template": "best_practices",
        "format": "markdown"
      }
    },
    {
      "plugin": "local",
      "task": "write_file",
      "params": {
        "path": "docs/best_practices.md",
        "content": "{content}"
      }
    }
  ]
}'
```

### Automated Code Improvement

Analyze, refactor, and test code changes:

```bash
python -m pepperpy.cli workflow run workflow/pipeline --input '{
  "steps": [
    {
      "plugin": "repository_analyzer",
      "task": "find_patterns",
      "params": {
        "repository_path": ".",
        "pattern_type": "anti_patterns"
      }
    },
    {
      "plugin": "content_generator",
      "task": "refactor_code",
      "params": {
        "anti_patterns": "{result}",
        "max_changes": 5
      }
    },
    {
      "plugin": "local",
      "task": "execute_command",
      "params": {
        "command": "pytest",
        "working_dir": "."
      }
    }
  ]
}'
```

## Conclusion

By combining PepperPy plugins, you can create powerful, automated workflows that leverage the strengths of multiple specialized tools. Whether through CLI commands, the pipeline plugin, or custom Python scripts, multi-plugin integration enables complex operations with minimal manual intervention.

For more examples and detailed information about each plugin, refer to the individual plugin documentation. 