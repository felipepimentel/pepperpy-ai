# Document Processing in PepperPy

This directory contains examples of document processing capabilities in the PepperPy framework.

## Standalone Document Processing Example

The `document_workflow_standalone.py` script demonstrates a simplified version of the document processing capabilities we implemented in the PepperPy framework.

This standalone implementation showcases the core document processing concepts without dependencies on the full PepperPy framework, making it easier to understand and test the functionality.

### Features Demonstrated

The example demonstrates the following document processing capabilities:

1. **Text Extraction**
   - Extract text from various document formats (TXT, MD, PDF, DOCX)
   - Graceful fallback for formats requiring unavailable dependencies
   - Document metadata capturing

2. **Document Classification**
   - Content-based classification by document type
   - Content category identification 
   - Language detection
   - Rule-based classification heuristics

3. **Metadata Extraction**
   - Date extraction using regex patterns
   - Basic entity extraction for people and organizations
   - Keyword extraction using frequency analysis
   - Smart filtering of stop words

4. **Pipeline Workflow Integration**
   - Flexible pipeline context for sharing data between stages
   - Modular processing stages with well-defined interfaces
   - Proper initialization and cleanup of resources
   - Error handling throughout the pipeline

### Running the Example

To run the standalone example:

```bash
python examples/document_workflow_standalone.py
```

The script will:
1. Create sample text and markdown files
2. Demonstrate text extraction
3. Classify the extracted document
4. Extract metadata from the document
5. Show how to chain these operations in a complete pipeline

## Full PepperPy Document Processing Implementation

In the full PepperPy framework, we've implemented a much more comprehensive document processing system with the following additional capabilities:

1. **Advanced Archive Handling**
   - Support for ZIP, TAR, RAR, and 7Z archives
   - Intelligent file filtering
   - Recursive extraction

2. **Sophisticated Batch Processing**
   - Parallel execution of document processing
   - Detailed results tracking
   - Comprehensive error handling

3. **Enhanced OCR**
   - Multi-language OCR capabilities
   - Image preprocessing options
   - Table extraction features

4. **Advanced Text Normalization**
   - 20+ normalization transformations
   - Unicode handling
   - Whitespace normalization
   - PII redaction
   - NLP-based processing

5. **Semantic Entity Extraction**
   - NLP-based entity and relationship extraction
   - Support for custom entity types
   - Confidence scoring for extracted entities

6. **Document Filtering**
   - Content-based filtering
   - Section-specific filtering
   - Metadata filtering

7. **Password-Protected Document Support**
   - Automatic decryption of protected documents
   - Secure password storage
   - Support for multiple protection schemes

8. **RAG Integration**
   - Seamless integration with Retrieval Augmented Generation
   - Document chunking and indexing
   - Vector store integration

The standalone example serves as a starting point for understanding these more advanced capabilities that are implemented in the full framework. 