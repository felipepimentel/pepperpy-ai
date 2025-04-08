# Content Generator Plugin

This plugin generates content using AI models based on prompts, templates, and input data. It can create blog posts, documentation, reports, and other text-based content.

## Basic CLI Usage

```bash
# Generate content with a simple prompt
python -m pepperpy.cli workflow run workflow/content_generator --input '{"task": "generate_content", "prompt": "Write a blog post about AI"}'
```

## Available Tasks

### Generate Content

Generates content based on a prompt.

```bash
python -m pepperpy.cli workflow run workflow/content_generator --input '{
  "task": "generate_content", 
  "prompt": "Write a blog post about AI",
  "format": "markdown",
  "max_length": 1000
}'
```

**Parameters:**
- `prompt` (string, required): The prompt describing the content to generate
- `format` (string, optional): Output format (markdown, html, text)
- `max_length` (integer, optional): Maximum content length in tokens
- `style` (string, optional): Writing style (formal, casual, technical)

### Generate From Template

Generates content using a template and variables.

```bash
python -m pepperpy.cli workflow run workflow/content_generator --input '{
  "task": "generate_from_template", 
  "template": "blog_post",
  "variables": {
    "title": "AI and the Future",
    "topic": "artificial intelligence",
    "key_points": ["machine learning", "neural networks", "ethical considerations"]
  }
}'
```

**Parameters:**
- `template` (string, required): Template name or path to template file
- `variables` (object, required): Variables to use in the template
- `format` (string, optional): Output format (markdown, html, text)

### Generate Documentation

Generates documentation for a project.

```bash
python -m pepperpy.cli workflow run workflow/content_generator --input '{
  "task": "generate_documentation", 
  "project_path": "/path/to/project",
  "doc_type": "api",
  "output_dir": "./docs"
}'
```

**Parameters:**
- `project_path` (string, required): Path to the project
- `doc_type` (string, optional): Type of documentation (api, user, dev)
- `output_dir` (string, optional): Directory to save generated documentation
- `include_patterns` (array, optional): Glob patterns for files to include
- `exclude_patterns` (array, optional): Glob patterns for files to exclude

## Configuration

You can customize the content generation with a configuration object:

```bash
python -m pepperpy.cli workflow run workflow/content_generator \
  --input '{"task": "generate_content", "prompt": "Write a blog post about AI"}' \
  --config '{
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "style_guide": "AP"
  }'
```

## Input Formats

The CLI supports different formats for providing input:

### JSON String
```bash
--input '{"task": "generate_content", "prompt": "Write a blog post about AI"}'
```

### JSON File
```bash
--input path/to/input.json
```

### Command-line Parameters
```bash
--params task=generate_content prompt="Write a blog post about AI"
```

## Output Format

The output is a JSON object with the following structure:

```json
{
  "title": "Generated Title",
  "content": "# Generated Content\n\nThis is the generated content...",
  "format": "markdown",
  "metadata": {
    "word_count": 500,
    "token_count": 750,
    "reading_time": "3 minutes"
  }
}
```

## Save Results to File

Save the generated content to a file:

```bash
python -m pepperpy.cli workflow run workflow/content_generator \
  --input '{
    "task": "generate_content", 
    "prompt": "Write a blog post about AI",
    "output_file": "blog_post.md"
  }'
```

## Advanced Usage

### Generate SEO-optimized Content

Generate content optimized for search engines:

```bash
python -m pepperpy.cli workflow run workflow/content_generator \
  --input '{
    "task": "generate_content", 
    "prompt": "Write a blog post about AI",
    "seo": {
      "keywords": ["artificial intelligence", "machine learning", "AI applications"],
      "target_audience": "technical professionals",
      "meta_description": "Learn about the latest AI advancements"
    }
  }'
```

### Content Refinement

Generate content with specific refinement requirements:

```bash
python -m pepperpy.cli workflow run workflow/content_generator \
  --input '{
    "task": "generate_content", 
    "prompt": "Write a technical guide about Docker",
    "refinements": ["technical_accuracy", "code_examples", "beginner_friendly"]
  }'
```

## Direct Usage in Python

For programmatic use or testing:

```python
import asyncio
from plugins.workflow.content_generator.workflow import ContentGeneratorWorkflow

async def generate_content():
    generator = ContentGeneratorWorkflow()
    await generator.initialize()
    
    try:
        result = await generator.execute({
            "task": "generate_content",
            "prompt": "Write a blog post about AI",
            "format": "markdown"
        })
        print(result["title"])
        print(result["content"])
    finally:
        await generator.cleanup()

if __name__ == "__main__":
    asyncio.run(generate_content())
```

## Troubleshooting

### Content Limits Exceeded

If you encounter "Content limits exceeded" errors:

1. Reduce the requested content length:
   ```bash
   python -m pepperpy.cli workflow run workflow/content_generator \
     --input '{
       "task": "generate_content", 
       "prompt": "Write a blog post about AI",
       "max_length": 500
     }'
   ```

2. Or split the content generation into smaller chunks:
   ```bash
   python -m pepperpy.cli workflow run workflow/content_generator \
     --input '{
       "task": "generate_content", 
       "prompt": "Write introduction for a blog post about AI",
       "max_length": 500
     }'
   ```

### Provider Not Found

If you get a "Provider not found" error:

1. List available workflows to check registration:
   ```bash
   python -m pepperpy.cli workflow list
   ```

2. Verify the plugin is correctly registered in the system.

## Further Documentation

For more detailed documentation, see [docs/workflows/content_generator.md](../../../docs/workflows/content_generator.md). 