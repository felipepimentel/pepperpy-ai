# Local Workflow Plugin

This plugin provides local file and resource management capabilities through the PepperPy framework. It allows you to perform operations on the local filesystem, execute commands, and manage local resources.

## Basic CLI Usage

```bash
# List files in a directory
python -m pepperpy.cli workflow run workflow/local --input '{"task": "list_files", "path": "."}'
```

## Available Tasks

### List Files

Lists files in a specified directory.

```bash
python -m pepperpy.cli workflow run workflow/local --input '{
  "task": "list_files", 
  "path": "/path/to/directory",
  "recursive": false,
  "pattern": "*.py"
}'
```

**Parameters:**
- `path` (string, required): Directory path to list files from
- `recursive` (boolean, optional): Whether to search recursively
- `pattern` (string, optional): Glob pattern to filter files
- `include_hidden` (boolean, optional): Whether to include hidden files
- `sort_by` (string, optional): Sort method (name, size, modified)

### Read File

Reads content from a file.

```bash
python -m pepperpy.cli workflow run workflow/local --input '{
  "task": "read_file", 
  "path": "/path/to/file.txt",
  "encoding": "utf-8"
}'
```

**Parameters:**
- `path` (string, required): Path to the file to read
- `encoding` (string, optional): File encoding (default: utf-8)
- `binary` (boolean, optional): Whether to read in binary mode
- `line_range` (array, optional): Range of lines to read [start, end]

### Write File

Writes content to a file.

```bash
python -m pepperpy.cli workflow run workflow/local --input '{
  "task": "write_file", 
  "path": "/path/to/output.txt",
  "content": "Content to write to the file",
  "mode": "w"
}'
```

**Parameters:**
- `path` (string, required): Path to the file to write
- `content` (string, required): Content to write to the file
- `mode` (string, optional): File open mode (w, a, wb, ab)
- `encoding` (string, optional): File encoding (default: utf-8)
- `make_dirs` (boolean, optional): Create parent directories if needed

### Execute Command

Executes a shell command locally.

```bash
python -m pepperpy.cli workflow run workflow/local --input '{
  "task": "execute_command", 
  "command": "ls -la",
  "working_dir": "/path/to/directory",
  "timeout": 30
}'
```

**Parameters:**
- `command` (string, required): Command to execute
- `working_dir` (string, optional): Working directory for the command
- `timeout` (integer, optional): Command timeout in seconds
- `environment` (object, optional): Environment variables
- `capture_output` (boolean, optional): Whether to capture command output

### Copy Files

Copies files or directories.

```bash
python -m pepperpy.cli workflow run workflow/local --input '{
  "task": "copy_files", 
  "source": "/path/to/source",
  "destination": "/path/to/destination",
  "recursive": true
}'
```

**Parameters:**
- `source` (string, required): Source path
- `destination` (string, required): Destination path
- `recursive` (boolean, optional): Whether to copy recursively
- `overwrite` (boolean, optional): Whether to overwrite existing files
- `preserve_metadata` (boolean, optional): Preserve file metadata

### File Search

Searches for files matching a pattern.

```bash
python -m pepperpy.cli workflow run workflow/local --input '{
  "task": "file_search", 
  "path": "/path/to/search",
  "pattern": "*.txt",
  "recursive": true,
  "max_results": 100
}'
```

**Parameters:**
- `path` (string, required): Path to search
- `pattern` (string, required): Glob pattern to match
- `recursive` (boolean, optional): Search recursively
- `max_results` (integer, optional): Maximum number of results
- `include_hidden` (boolean, optional): Include hidden files

## Configuration

You can customize the local workflow with a configuration object:

```bash
python -m pepperpy.cli workflow run workflow/local \
  --input '{"task": "list_files", "path": "."}' \
  --config '{
    "safe_mode": true,
    "default_encoding": "utf-8",
    "max_file_size": 10485760,
    "command_timeout": 60
  }'
```

## Input Formats

The CLI supports different formats for providing input:

### JSON String
```bash
--input '{"task": "list_files", "path": "."}'
```

### JSON File
```bash
--input path/to/input.json
```

### Command-line Parameters
```bash
--params task=list_files path=.
```

## Output Format

The output is a JSON object with the following structure:

```json
{
  "result": {
    "success": true,
    "data": [
      {
        "name": "file1.txt",
        "path": "/path/to/file1.txt",
        "size": 1024,
        "modified": "2023-01-01T12:00:00",
        "type": "file"
      },
      {
        "name": "directory1",
        "path": "/path/to/directory1",
        "modified": "2023-01-01T12:00:00",
        "type": "directory"
      }
    ]
  },
  "metadata": {
    "count": 2,
    "execution_time": "0.005s"
  }
}
```

For specific tasks, the structure of the `data` field will vary.

## Save Results to File

Save command output to a file:

```bash
python -m pepperpy.cli workflow run workflow/local \
  --input '{
    "task": "execute_command", 
    "command": "ls -la",
    "output_file": "command_results.json"
  }'
```

## Advanced Usage

### Bulk File Operations

Perform operations on multiple files:

```bash
python -m pepperpy.cli workflow run workflow/local \
  --input '{
    "task": "bulk_operation", 
    "operation": "rename",
    "files": [
      {"source": "file1.txt", "destination": "new_file1.txt"},
      {"source": "file2.txt", "destination": "new_file2.txt"}
    ],
    "continue_on_error": true
  }'
```

### File Watching

Watch a directory for changes:

```bash
python -m pepperpy.cli workflow run workflow/local \
  --input '{
    "task": "watch_directory", 
    "path": "/path/to/watch",
    "pattern": "*.log",
    "events": ["create", "modify"],
    "duration": 3600,
    "callback": {
      "task": "execute_command",
      "command": "echo 'File changed: $FILE'"
    }
  }'
```

## Direct Usage in Python

For programmatic use or testing:

```python
import asyncio
from plugins.workflow.local.workflow import LocalWorkflow

async def list_files():
    workflow = LocalWorkflow()
    await workflow.initialize()
    
    try:
        result = await workflow.execute({
            "task": "list_files",
            "path": "/path/to/directory",
            "recursive": True,
            "pattern": "*.py"
        })
        
        for file_info in result["result"]["data"]:
            print(f"{file_info['name']} - {file_info['size']} bytes")
    finally:
        await workflow.cleanup()

if __name__ == "__main__":
    asyncio.run(list_files())
```

## Troubleshooting

### Permission Issues

If you encounter permission errors:

1. Check file and directory permissions:
   ```bash
   python -m pepperpy.cli workflow run workflow/local \
     --input '{
       "task": "execute_command", 
       "command": "ls -la /path/to/check"
     }'
   ```

2. Run the workflow with appropriate permissions.

### Path Not Found

If paths are not found:

1. Check that the path exists and is accessible:
   ```bash
   python -m pepperpy.cli workflow run workflow/local \
     --input '{
       "task": "list_files", 
       "path": "/path/to/verify"
     }'
   ```

2. Use absolute paths to avoid confusion.

### Command Execution Issues

If commands fail to execute:

1. Test the command directly in a terminal
2. Check if the command requires specific environment variables:
   ```bash
   python -m pepperpy.cli workflow run workflow/local \
     --input '{
       "task": "execute_command", 
       "command": "my_command",
       "environment": {
         "PATH": "/usr/local/bin:/usr/bin:/bin"
       }
     }'
   ```

## Further Documentation

For more detailed documentation, see [docs/workflows/local.md](../../../docs/workflows/local.md). 