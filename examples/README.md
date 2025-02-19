# Pepperpy Examples

This directory contains example scripts demonstrating various capabilities of the Pepperpy framework.

## Available Examples

### News Podcast Generator (`news_podcast.py`)
Demonstrates how to create an automated news podcast generator that:
- Fetches news from RSS feeds
- Generates natural podcast scripts
- Synthesizes speech with effects
- Caches results for efficiency

Features:
- Content fetching and processing
- LLM-based script generation
- Text-to-speech synthesis
- Memory caching
- Error handling and logging
- Resource management

## Installation

1. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

2. Set up required environment variables:
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```

## Running Examples

Navigate to the examples directory and run any example using Poetry:

```bash
cd examples
poetry run python news_podcast.py
```

## Configuration

Each example can be configured through environment variables or by modifying the script directly. Common configuration options include:

- `OPENAI_API_KEY`: Your OpenAI API key
- `PEPPERPY_OUTPUT_DIR`: Custom output directory
- `PEPPERPY_CACHE_DIR`: Custom cache directory

## Development

When creating new examples:

1. Follow the example template structure:
   - Comprehensive docstring with purpose, requirements, and usage
   - Proper error handling and logging
   - Resource cleanup
   - Type hints and documentation

2. Update dependencies if needed:
   ```bash
   poetry add package-name
   ```

3. Test the example:
   ```bash
   poetry run pytest tests/examples/test_your_example.py
   ```

## Troubleshooting

Common issues and solutions:

1. **Poetry Not Found**
   - Ensure Poetry is installed: `curl -sSL https://install.python-poetry.org | python3 -`

2. **Dependencies Issues**
   - Update Poetry: `poetry self update`
   - Clean and reinstall: `poetry env remove && poetry install`

3. **API Key Issues**
   - Check if environment variables are set: `echo $OPENAI_API_KEY`
   - Ensure API key has required permissions

4. **Resource Issues**
   - Check disk space for output files
   - Verify memory cache directory permissions

## Contributing

When adding new examples:

1. Follow the example standards in `rules/302-examples.xml`
2. Include comprehensive documentation
3. Add appropriate tests
4. Update this README with the new example

## License

All examples are licensed under the same terms as the Pepperpy project. 