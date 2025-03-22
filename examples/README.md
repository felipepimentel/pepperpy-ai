# PepperPy Examples

This directory contains examples demonstrating the capabilities of the PepperPy framework through practical, real-world use cases.

## PDI Assistant Example

The `pdi_assistant_example.py` demonstrates a Professional Development Initiative (PDI) assistant that:

1. **Manages Development Plans**
   - Creates personalized PDIs based on user goals
   - Tracks progress and provides recommendations
   - Uses RAG for context-aware assistance

2. **Leverages RAG Providers**
   - Uses AnnoyRAGProvider (default) for efficient vector search
   - Supports multiple provider options:
     - FAISS for high-performance needs
     - SQLite for simple persistence
     - Chroma for feature-rich storage
     - Local for testing
     - OpenAI and Pinecone for cloud-based solutions

3. **Handles Storage**
   - Uses LocalStorageProvider for file persistence
   - Supports multiple storage backends

## Content Pipeline Example

The `podcast_generator_example.py` demonstrates a content generation pipeline that:

1. **Fetches and Analyzes News**
   - Collects recent news articles about a specific topic
   - Analyzes content for key themes and insights
   - Identifies trends and patterns

2. **Creates Podcast Content**
   - Transforms articles into natural dialogue
   - Adds proper transitions and flow
   - Includes production cues and markers

3. **Produces Audio Output**
   - Converts script to natural speech
   - Handles multiple speakers
   - Adds appropriate pacing and emphasis

## Running the Examples

### Prerequisites

1. Install PepperPy with all optional dependencies:
   ```bash
   pip install pepperpy[all]
   ```

2. Set up required environment variables:
   ```bash
   # For podcast generator example
   export PEPPERPY_NEWS__NEWSAPI_API_KEY=your_api_key  # Required for news fetching
   export PEPPERPY_TTS__PROVIDER=your_provider  # e.g., "murf"
   export PEPPERPY_TTS_MURF__API_KEY=your_key  # If using Murf
   ```

### Running the Examples

```bash
# Run the PDI assistant example
python examples/pdi_assistant_example.py

# Run the podcast generator example
python examples/podcast_generator_example.py
```

## Example Output

The examples produce:

1. **PDI Assistant**
   - Professional development plan
   - Action items and deadlines
   - Learning resources and recommendations

2. **Podcast Generator**
   - Podcast script (text format)
   - Audio file (MP3 format)
   - Progress updates and statistics

## Customization

You can customize the examples by:

1. Changing RAG providers in PDI assistant:
   ```python
   # Use FAISS for high performance
   assistant = PDIAssistant(rag_provider=FAISSRAGProvider())
   
   # Use Chroma for persistence
   assistant = PDIAssistant(rag_provider=ChromaRAGProvider())
   ```

2. Modifying podcast topics:
   ```python
   pipeline = ContentPipeline("Your topic here")
   ```

3. Adjusting TTS settings:
   ```python
   await convert_text(text, voice_id="your-voice-id")
   ```

## Support

For questions about the examples:
- Check the [documentation](https://pepperpy.readthedocs.io)
- Open an issue on GitHub
- Join our community Discord server 