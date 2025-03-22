# PepperPy Examples

This directory contains examples demonstrating the capabilities of the PepperPy framework through practical, real-world use cases.

## Content Pipeline Example

The main example `content_pipeline.py` demonstrates a complete content generation pipeline that:

1. **Fetches and Analyzes News**
   - Collects recent news articles about a specific topic
   - Analyzes content for key themes and insights
   - Identifies trends and patterns

2. **Generates Structured Discussion**
   - Creates a multi-perspective debate
   - Synthesizes arguments and counterarguments
   - Provides balanced analysis

3. **Creates Podcast Content**
   - Transforms discussion into natural dialogue
   - Adds proper transitions and flow
   - Includes production cues and markers

4. **Produces Audio Output**
   - Converts script to natural speech
   - Handles multiple speakers
   - Adds appropriate pacing and emphasis

## Running the Example

### Prerequisites

1. Install PepperPy with all optional dependencies:
   ```bash
   pip install pepperpy[all]
   ```

2. Set up required environment variables:
   ```bash
   export NEWSAPI_KEY=your_api_key  # Required for news fetching
   export PEPPERPY_API_KEY=your_key  # Required for PepperPy services
   ```

### Running the Pipeline

```bash
# Run the complete content pipeline
python examples/content_pipeline.py
```

The pipeline will:
- Fetch today's news about AI
- Generate a comprehensive analysis
- Create a podcast script
- Produce an audio file

## Example Output

The example produces:

1. **Console Output**
   - Progress updates for each stage
   - Timing information
   - Summary statistics

2. **Generated Files**
   - Podcast script (text format)
   - Audio file (MP3 format)

## Customization

You can customize the pipeline by:

1. Changing the topic:
   ```python
   pipeline = ContentPipeline("Your topic here")
   ```

2. Modifying the time range for news:
   ```python
   articles = await pipeline.fetch_news(days=7)  # Last week's news
   ```

3. Adjusting the perspectives:
   ```python
   perspectives = ["Your", "Custom", "Perspectives"]
   ```

## Support

For questions about the example:
- Check the [documentation](https://pepperpy.readthedocs.io)
- Open an issue on GitHub
- Join our community Discord server 