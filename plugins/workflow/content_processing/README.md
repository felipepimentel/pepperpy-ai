# Content Processing Workflow

A workflow plugin for processing textual content through multiple stages:

1. Text extraction from documents
2. Text normalization 
3. Content generation
4. Content summarization

## Features

- Extract key information from documents
- Normalize text with consistent terminology and formatting
- Generate new content based on input and prompts
- Create concise summaries of longer documents

## Configuration

The workflow can be configured with these options:

- `output_dir`: Directory to save processing results (default: "./output/content")
- `auto_save_results`: Whether to automatically save results to files (default: true)
- `log_level`: Logging level (default: INFO)
- `log_to_console`: Whether to log to console (default: true)

## Usage

### Via Python API

```python
from pepperpy.workflow import create_provider

# Create the content processing workflow provider
workflow = create_provider("content_processing", 
                           output_dir="./output/content")

# Create input for processing
input_data = {
    "task": "process_content",
    "input": {
        "content": "Your content to process here...",
        "processors": [
            {
                "type": "text_normalization",
                "prompt": "Normalize this text with consistent terminology",
                "output": "normalized.txt"
            },
            {
                "type": "content_summarization",
                "prompt": "Summarize this content briefly",
                "parameters": {"sentences": 3},
                "output": "summary.txt"
            }
        ]
    }
}

# Execute workflow
result = await workflow.execute(input_data)

# Print the summary
print(result["results"]["content_summarization"])
```

### Via CLI

```bash
python -m pepperpy.cli workflow run workflow/content_processing \
  --params "content=My content to process" \
  --params "task=process_content"
```

## Requirements

- nltk>=3.8.1
- spacy>=3.7.1
- beautifulsoup4>=4.12.2
- pydantic>=2.0.0
- jsonschema>=4.0.0 