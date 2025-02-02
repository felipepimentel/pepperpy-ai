# Pepperpy Examples

This directory contains examples demonstrating how to use the Pepperpy library.

## Simple Chat Example

The `simple_chat.py` example shows how to create a basic chat application using OpenRouter as the provider, with support for fallback models.

### Prerequisites

1. Make sure you have Pepperpy installed:
   ```bash
   pip install pepperpy
   ```

2. Set up your API keys and configuration in a `.env` file:
   ```bash
   # PepperPy API Keys (for LLM)
   PEPPERPY_API_KEY=your-openrouter-api-key
   PEPPERPY_PROVIDER=openrouter
   PEPPERPY_MODEL=google/gemini-2.0-flash-exp:free

   # Fallback Provider (Optional)
   PEPPERPY_FALLBACK_PROVIDER=openrouter
   PEPPERPY_FALLBACK_MODEL=openai/gpt-4-mini
   PEPPERPY_FALLBACK_API_KEY=your-fallback-api-key
   ```

### Running the Example

To run the simple chat example:

```bash
python simple_chat.py
```

The example will:
1. Load your OpenRouter API key and configuration from the environment
2. Initialize the primary provider (and fallback if configured)
3. Start an interactive chat session where you can:
   - Type messages and get responses from the model
   - See the responses streamed in real-time
   - Automatically fall back to a backup model if the primary fails
   - Type 'exit' to quit the chat

### Code Explanation

The example demonstrates:
- How to configure and initialize OpenRouter providers
- How to implement fallback support for reliability
- How to use streaming responses for real-time output
- Proper error handling and graceful degradation
- Environment variable configuration
- Resource cleanup
- Type hints and documentation

## Features Demonstrated

- Provider initialization and configuration
- Streaming responses
- Environment variable usage
- Error handling
- Resource cleanup
- Type hints and documentation 