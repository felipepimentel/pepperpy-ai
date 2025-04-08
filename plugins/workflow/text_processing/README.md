# Text Processing Plugin

The Text Processing plugin provides sophisticated natural language processing capabilities for analyzing, transforming, and understanding text data.

## Basic CLI Usage

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "analyze_sentiment",
  "text": "I absolutely love the new features in this software update. Very impressive work!",
  "model": "default"
}'
```

## Available Tasks

### Analyze Text

Perform comprehensive text analysis including sentiment, entities, keywords, and more.

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "analyze_text",
  "text": "Apple Inc. is planning to open a new headquarters in Austin, Texas by 2022. CEO Tim Cook announced the $1 billion investment yesterday.",
  "analysis_types": [
    "sentiment", 
    "entities", 
    "keywords", 
    "syntax", 
    "categories"
  ],
  "language": "en",
  "model": "comprehensive"
}'
```

### Analyze Sentiment

Analyze sentiment in text to determine if it's positive, negative, or neutral.

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "analyze_sentiment",
  "text": "The customer service team was extremely helpful and resolved my issue quickly.",
  "model": "detailed",  # Options: basic, default, detailed
  "language": "en",
  "aspects": ["service", "speed", "resolution"]  # Optional: Extract sentiment for specific aspects
}'
```

### Extract Entities

Identify and extract named entities from text.

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "extract_entities",
  "text": "Microsoft CEO Satya Nadella announced a new partnership with OpenAI in Seattle on Monday.",
  "entity_types": ["PERSON", "ORG", "DATE", "LOC", "PRODUCT"],  # Optional: Filter specific entity types
  "confidence_threshold": 0.7,  # Optional: Minimum confidence score (0-1)
  "include_metadata": true  # Include entity metadata like Wikipedia links
}'
```

### Summarize Text

Generate concise summaries of longer text.

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "summarize",
  "text": "Long text to summarize...",
  "max_length": 200,  # Maximum length of summary in characters
  "min_length": 50,   # Minimum length of summary in characters
  "format": "paragraph",  # Options: paragraph, bullets, headline
  "focus": ["main_points", "conclusions"]  # Optional: Focus on specific aspects
}'
```

### Extract Keywords

Extract important keywords and phrases from text.

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "extract_keywords",
  "text": "Quantum computing leverages quantum mechanics principles like superposition and entanglement to process information in ways classical computers cannot.",
  "max_keywords": 10,  # Maximum number of keywords to extract
  "include_ngrams": true,  # Include multi-word phrases
  "include_scores": true,  # Include relevance scores
  "exclude_stopwords": true  # Exclude common words
}'
```

### Classify Text

Categorize text into predefined or custom categories.

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "classify_text",
  "text": "The latest smartphone features a 108MP camera with night mode and 8K video recording capabilities.",
  "taxonomy": "iab",  # Options: iab (standard categories), custom
  "custom_categories": ["Technology", "Photography", "Consumer Electronics"],  # Used when taxonomy is "custom"
  "threshold": 0.3,  # Minimum confidence threshold
  "multi_label": true  # Allow multiple categories
}'
```

### Transform Text

Apply various transformations to text.

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "transform_text",
  "text": "The quick brown fox jumps over the lazy dog.",
  "transforms": [
    {"type": "translate", "target_language": "es"},
    {"type": "formality", "level": "formal"},
    {"type": "expand", "factor": 1.5},
    {"type": "simplify", "level": "elementary"}
  ]
}'
```

### Extract Information

Extract structured information from text using templates or patterns.

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "extract_information",
  "text": "Meeting scheduled for July 15, 2023, at 2:30 PM with John Smith (john.smith@example.com) to discuss the Q3 marketing budget of $250,000.",
  "extractors": [
    {"type": "date", "format": "ISO"},
    {"type": "time", "format": "24h"},
    {"type": "email"},
    {"type": "monetary_value"},
    {"type": "custom_pattern", "pattern": "Q[1-4]\\s+\\w+"}
  ],
  "output_format": "json"
}'
```

## Configuration Options

Customize the text processing behavior with these options:

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "analyze_text",
  "text": "Text to analyze...",
  "config": {
    "model": "advanced",  # Model to use (basic, default, advanced)
    "language": "en",     # Language code (auto for automatic detection)
    "cache": true,        # Cache results to avoid duplicate processing
    "cache_ttl": 86400,   # Cache time-to-live in seconds (1 day)
    "batch_size": 10,     # Process texts in batches of this size
    "log_level": "info",  # Logging verbosity (debug, info, warning, error)
    "timeout": 30         # Maximum processing time in seconds
  }
}'
```

## Input Format

The CLI accepts input in the following format:

```json
{
  "task": "task_name",  // Required: The specific task to perform
  "text": "text_to_process",  // Required: The text to process (or file path)
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
    "task_result": {},  // Task-specific results
    "metadata": {
      "processing_time": "0.234s",
      "model": "default",
      "language": "en",
      "text_length": 423
    }
  },
  "error": null  // Error message if status is "error"
}
```

## Saving Results to File

To save the results to a file, use the `--output` parameter:

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "analyze_sentiment",
  "text": "This is amazing!"
}' --output "sentiment_analysis.json"
```

## Advanced Usage

### Batch Processing

Process multiple texts in a single request:

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "batch_process",
  "texts": [
    "First text to analyze.",
    "Second text to analyze.",
    "Third text to analyze."
  ],
  "operation": {
    "task": "analyze_sentiment"
  },
  "config": {
    "parallel": true,
    "max_parallel": 5
  }
}'
```

### Text Processing Pipeline

Create a multi-step text processing pipeline:

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "pipeline",
  "text": "Original text that needs multiple processing steps.",
  "steps": [
    {
      "task": "transform_text",
      "transforms": [
        {"type": "normalize", "operations": ["lowercase", "remove_punctuation"]}
      ]
    },
    {
      "task": "extract_keywords",
      "max_keywords": 5
    },
    {
      "task": "summarize",
      "max_length": 100
    }
  ],
  "return_intermediate_results": true
}'
```

### Advanced Document Processing

Process complex documents with multiple sections:

```bash
python -m pepperpy.cli workflow run workflow/text_processing --input '{
  "task": "process_document",
  "source": "document.pdf",  # Can be file path or previously loaded document
  "operations": [
    {"type": "split_sections", "method": "headings"},
    {"type": "analyze_each", "task": "extract_entities"},
    {"type": "summarize_sections", "max_length_per_section": 100},
    {"type": "aggregate", "method": "hierarchical"}
  ],
  "output_format": "structured"
}'
```

## Python Usage

You can also use the plugin directly in Python:

```python
import asyncio
from pepperpy.plugin.registry import PluginRegistry
from pepperpy.plugin.discovery import discover_plugins

async def process_text():
    await discover_plugins()
    registry = PluginRegistry()
    
    processor = await registry.create_provider_instance("workflow", "text_processing")
    
    try:
        result = await processor.execute({
            "task": "analyze_sentiment",
            "text": "I'm extremely satisfied with the quality of service provided.",
            "model": "detailed"
        })
        
        print(f"Overall sentiment: {result['result']['sentiment']}")
        print(f"Confidence: {result['result']['confidence']}")
        
        if "aspects" in result["result"]:
            print("\nAspect sentiments:")
            for aspect, data in result["result"]["aspects"].items():
                print(f"- {aspect}: {data['sentiment']} (confidence: {data['confidence']})")
        
        return result
    finally:
        await processor.cleanup()

if __name__ == "__main__":
    result = asyncio.run(process_text())
```

## Troubleshooting

### Language Support Issues

If you encounter language-related errors:

1. Check that the specified language code is supported
2. Use `"language": "auto"` for automatic language detection
3. For specialized language models, check documentation for supported languages

### Processing Large Texts

For large documents or long texts:

1. Break down text into smaller chunks using the `split_text` task
2. Increase the `timeout` configuration value
3. Consider using document processing features with automatic chunking

### Model Availability

If you encounter model-related errors:

1. Check that the specified model is available in your installation
2. Fall back to the "default" model which is guaranteed to be available
3. For advanced models, ensure you have the required dependencies installed

## Further Documentation

For more detailed documentation, see the [Text Processing Documentation](docs/plugins/text_processing/index.md). 