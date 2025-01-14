# Text Processing

PepperPy AI provides comprehensive text processing capabilities for handling and analyzing text data.

## Overview

The text processing system offers:
- Text analysis
- Text chunking
- Text preprocessing
- Content extraction
- Semantic analysis

## Core Components

### Text Processor

The main text processing interface:

```python
from pepperpy.text import TextProcessor
from pepperpy.config import Config

async def process_example():
    config = Config()
    processor = TextProcessor(config)
    
    # Process text
    result = await processor.process(
        "Your text here",
        clean=True,
        normalize=True
    )
```

### Text Analyzer

Advanced text analysis capabilities:

```python
from pepperpy.text import TextAnalyzer

async def analysis_example():
    analyzer = TextAnalyzer()
    
    # Analyze text
    analysis = await analyzer.analyze(
        "Sample text for analysis",
        include_sentiment=True,
        extract_entities=True
    )
    
    print("Sentiment:", analysis.sentiment)
    print("Entities:", analysis.entities)
```

### Text Chunker

Split text into manageable chunks:

```python
from pepperpy.text import TextChunker

async def chunking_example():
    chunker = TextChunker(
        chunk_size=1000,
        overlap=100
    )
    
    # Split text into chunks
    chunks = await chunker.chunk(
        "Long text content...",
        respect_sentences=True
    )
```

## Configuration

Configure text processing:

```python
from pepperpy.text.config import TextConfig

config = TextConfig(
    chunk_size=1000,
    overlap=100,
    clean_text=True,
    normalize=True,
    language="en"
)
```

## Advanced Features

### Content Extraction

```python
from pepperpy.text import ContentExtractor

async def extraction_example():
    extractor = ContentExtractor()
    
    # Extract specific content
    content = await extractor.extract(
        text="Sample text with [key information]",
        patterns=["[...]", "key: value"],
        include_metadata=True
    )
```

### Semantic Analysis

```python
from pepperpy.text import SemanticAnalyzer

async def semantic_example():
    analyzer = SemanticAnalyzer()
    
    # Analyze semantic meaning
    semantics = await analyzer.analyze(
        "Text for semantic analysis",
        extract_topics=True,
        analyze_structure=True
    )
```

### Text Preprocessing

```python
from pepperpy.text import TextPreprocessor

async def preprocessing_example():
    preprocessor = TextPreprocessor()
    
    # Preprocess text
    processed = await preprocessor.preprocess(
        text="Raw text input",
        steps=[
            "clean",
            "normalize",
            "tokenize",
            "remove_stopwords"
        ]
    )
```

## Best Practices

1. **Text Handling**
   - Clean text before processing
   - Handle different encodings
   - Respect language specifics

2. **Chunking**
   - Choose appropriate chunk sizes
   - Consider content boundaries
   - Manage overlaps carefully

3. **Performance**
   - Batch process when possible
   - Cache processed results
   - Use async operations

4. **Quality**
   - Validate input text
   - Handle edge cases
   - Preserve important formatting

## Environment Variables

Configure text processing:

```bash
PEPPERPY_TEXT_CHUNK_SIZE=1000
PEPPERPY_TEXT_OVERLAP=100
PEPPERPY_TEXT_CLEAN=true
PEPPERPY_TEXT_LANGUAGE=en
```

## Examples

### Document Processing

```python
from pepperpy.text import DocumentProcessor

async def document_example():
    processor = DocumentProcessor()
    
    # Process document
    result = await processor.process_document(
        "document.txt",
        extract_metadata=True,
        analyze_content=True
    )
    
    print("Title:", result.metadata.title)
    print("Summary:", result.summary)
    print("Key points:", result.key_points)
```

### Language Detection

```python
from pepperpy.text import LanguageDetector

async def language_example():
    detector = LanguageDetector()
    
    # Detect language
    language = await detector.detect(
        "Text in any language",
        confidence_threshold=0.8
    )
    
    print("Language:", language.code)
    print("Confidence:", language.confidence)
```

### Text Summarization

```python
from pepperpy.text import TextSummarizer

async def summarization_example():
    summarizer = TextSummarizer()
    
    # Generate summary
    summary = await summarizer.summarize(
        "Long text to summarize...",
        max_length=200,
        focus_points=["key concepts", "conclusions"]
    )
    
    print("Summary:", summary)
    print("Length:", len(summary))
``` 