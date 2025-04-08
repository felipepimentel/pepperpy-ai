# Data Processing Plugin

The Data Processing plugin provides powerful capabilities to load, transform, analyze, and export data from various sources and formats.

## Basic CLI Usage

```bash
python -m pepperpy.cli workflow run workflow/data_processing --input '{
  "task": "analyze_data",
  "source": "data.csv",
  "analysis": [
    {"type": "summary", "columns": ["revenue", "expenses", "profit"]},
    {"type": "correlation", "columns": ["marketing_spend", "sales"]}
  ]
}'
```

## Available Tasks

### Load Data

Load data from a specified source.

```bash
python -m pepperpy.cli workflow run workflow/data_processing --input '{
  "task": "load_data",
  "source": "path/to/data.csv",  # or URL, database connection string
  "format": "csv",  # Options: csv, json, excel, parquet, sql
  "options": {
    "delimiter": ",",
    "has_header": true,
    "sheet_name": "Sheet1",  # For Excel files
    "query": "SELECT * FROM users",  # For SQL sources
    "connection_params": {}  # Database connection parameters
  }
}'
```

### Analyze Data

Perform analysis on a dataset.

```bash
python -m pepperpy.cli workflow run workflow/data_processing --input '{
  "task": "analyze_data",
  "source": "data.csv",  # File path or data loaded in a previous step
  "analysis": [
    {"type": "summary", "columns": ["age", "income", "spending"]},
    {"type": "distribution", "column": "age"},
    {"type": "correlation", "columns": ["income", "spending"]},
    {"type": "aggregate", "operation": "mean", "column": "income", "group_by": "region"}
  ],
  "filters": [
    {"column": "age", "operator": ">", "value": 18},
    {"column": "region", "operator": "in", "value": ["North", "South"]}
  ]
}'
```

### Transform Data

Transform data with specified operations.

```bash
python -m pepperpy.cli workflow run workflow/data_processing --input '{
  "task": "transform_data",
  "source": "data.csv",
  "operations": [
    {"type": "filter", "column": "status", "operator": "==", "value": "active"},
    {"type": "select", "columns": ["id", "name", "age", "status"]},
    {"type": "rename", "columns": {"id": "user_id", "name": "full_name"}},
    {"type": "calculate", "name": "age_group", "expression": "age // 10 * 10"},
    {"type": "normalize", "columns": ["income", "spending"]},
    {"type": "fillna", "column": "age", "value": 30},
    {"type": "sort", "by": ["age_group", "income"], "ascending": [true, false]}
  ],
  "output": "transformed_data.csv",
  "output_format": "csv"
}'
```

### Visualize Data

Create visualizations from data.

```bash
python -m pepperpy.cli workflow run workflow/data_processing --input '{
  "task": "visualize_data",
  "source": "data.csv",
  "visualizations": [
    {"type": "bar", "x": "category", "y": "count", "title": "Category Distribution"},
    {"type": "line", "x": "date", "y": ["revenue", "expenses"], "title": "Financial Trends"},
    {"type": "scatter", "x": "marketing", "y": "sales", "title": "Marketing Impact"},
    {"type": "pie", "values": "market_share", "labels": "company", "title": "Market Share"},
    {"type": "heatmap", "x": "day", "y": "hour", "values": "traffic", "title": "Traffic Patterns"}
  ],
  "output": "visualizations.pdf",  # Options: png, jpg, pdf, html
  "theme": "light",  # Options: light, dark, blue, etc.
  "size": [1200, 800]  # Width and height in pixels
}'
```

### Export Data

Export data to various formats.

```bash
python -m pepperpy.cli workflow run workflow/data_processing --input '{
  "task": "export_data",
  "source": "processed_data",  # Data from previous step or file path
  "output": "output_data",  # Output file path without extension
  "format": "csv",  # Options: csv, json, excel, parquet, sql
  "options": {
    "delimiter": ",",
    "include_header": true,
    "sheet_name": "Processed Data",
    "compression": "gzip",  # For supported formats
    "table_name": "processed_data",  # For SQL export
    "if_exists": "replace"  # For SQL export (replace, append, fail)
  }
}'
```

## Configuration Options

You can customize the data processing behavior with these options:

```bash
python -m pepperpy.cli workflow run workflow/data_processing --input '{
  "task": "transform_data",
  "source": "data.csv",
  "operations": [...],
  "config": {
    "chunk_size": 10000,  # Process data in chunks for large datasets
    "parallel": true,  # Enable parallel processing
    "log_level": "info",  # Logging verbosity (debug, info, warning, error)
    "temp_dir": "/tmp/data_processing",  # Directory for temporary files
    "memory_limit": "4G"  # Maximum memory usage
  }
}'
```

## Input Format

The CLI accepts input in the following format:

```json
{
  "task": "task_name",  // Required: The specific task to perform
  "source": "data_source",  // Required: Path, URL, or data reference
  "task_specific_parameters": {},  // Parameters specific to the task
  "config": {}  // Optional: Configuration options
}
```

## Output Format

The plugin returns a JSON object with the following structure:

```json
{
  "status": "success",  // or "error"
  "result": {
    "data": [],  // Processed data or analysis results
    "metadata": {
      "rows": 1000,
      "columns": 15,
      "processing_time": "2.3s"
    }
  },
  "visualizations": {
    "files": ["chart1.png", "chart2.png"],
    "html": "<div>...</div>"  // For HTML visualizations
  },
  "exports": {
    "files": ["output.csv"]
  },
  "error": null  // Error message if status is "error"
}
```

## Saving Results to File

To save the results to a file, use the `--output` parameter:

```bash
python -m pepperpy.cli workflow run workflow/data_processing --input '{
  "task": "analyze_data",
  "source": "data.csv",
  "analysis": [{"type": "summary"}]
}' --output "analysis_results.json"
```

## Advanced Usage

### Creating a Data Pipeline

Combine multiple operations in sequence:

```bash
python -m pepperpy.cli workflow run workflow/data_processing --input '{
  "task": "pipeline",
  "steps": [
    {
      "task": "load_data",
      "source": "data.csv",
      "format": "csv"
    },
    {
      "task": "transform_data",
      "operations": [
        {"type": "filter", "column": "status", "operator": "==", "value": "active"},
        {"type": "calculate", "name": "full_name", "expression": "first_name + \" \" + last_name"}
      ]
    },
    {
      "task": "analyze_data",
      "analysis": [{"type": "summary"}]
    },
    {
      "task": "export_data",
      "output": "processed_data",
      "format": "json"
    }
  ]
}'
```

### Database Integration

Work directly with database sources:

```bash
python -m pepperpy.cli workflow run workflow/data_processing --input '{
  "task": "load_data",
  "source": "postgresql://user:password@localhost:5432/mydatabase",
  "format": "sql",
  "options": {
    "query": "SELECT * FROM sales WHERE date >= '2023-01-01'"
  }
}'
```

## Python Usage

You can also use the plugin directly in Python:

```python
import asyncio
from pepperpy.plugin.registry import PluginRegistry
from pepperpy.plugin.discovery import discover_plugins

async def process_data():
    await discover_plugins()
    registry = PluginRegistry()
    
    processor = await registry.create_provider_instance("workflow", "data_processing")
    
    try:
        result = await processor.execute({
            "task": "transform_data",
            "source": "data.csv",
            "operations": [
                {"type": "filter", "column": "status", "operator": "==", "value": "active"},
                {"type": "select", "columns": ["id", "name", "email", "status"]}
            ],
            "output": "filtered_data.csv"
        })
        
        return result
    finally:
        await processor.cleanup()

if __name__ == "__main__":
    result = asyncio.run(process_data())
    print(f"Data processing completed: {result['status']}")
```

## Troubleshooting

### Data Format Issues

If you encounter format-related errors:

1. Check that your source data is in the expected format
2. Verify that all required columns exist in your dataset
3. For CSV files, ensure the delimiter matches your file format

### Memory Limitations

For large datasets:

1. Use the `chunk_size` configuration option to process data in smaller batches
2. Increase the `memory_limit` if your system has sufficient resources
3. Consider using file-based operations rather than loading all data into memory

### Provider Not Found

If you see "Provider not found" errors:

1. Ensure the data_processing plugin is correctly installed
2. Run `python -m pepperpy.cli workflow list` to verify the plugin is registered
3. Check that you're using the correct workflow name: `workflow/data_processing`

## Further Documentation

For more detailed documentation, see the [Data Processing Documentation](docs/plugins/data_processing/index.md). 