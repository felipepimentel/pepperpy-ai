# PepperPy Examples

This directory contains example applications demonstrating how to use different features of the PepperPy framework.

## Prerequisites

Before running any examples, ensure you have:

1. Python 3.10+ installed
2. PepperPy installed (`pip install -e ..` from this directory)
3. Any required API keys (see specific example requirements)

## Available Examples

### LLM Examples

- `llm_completion_example.py` - Demonstrates basic chat completion with OpenAI
- `llm_stream_example.py` - Shows how to stream responses from OpenAI
- `llm_embedding_example.py` - Shows how to generate and compare embeddings with OpenAI
- `chatbot_example.py` - Interactive chatbot with conversation history and streaming responses

### TTS Examples

- `tts_example.py` - Shows how to use Text-to-Speech with Azure

### Multi-Provider Examples

- `multi_provider_example.py` - Demonstrates using multiple providers together

## Running the Examples

To run an example:

```bash
# Set necessary environment variables first
export OPENAI_API_KEY=your_key_here
export AZURE_API_KEY=your_azure_key_here

# Then run the example
python llm_completion_example.py
```

## Creating Your Own Applications

You can use these examples as a starting point for your own applications. The key steps are:

1. Import the PepperPy facade:
   ```python
   from pepperpy import PepperPy
   ```

2. Configure with desired providers:
   ```python
   pepper = PepperPy()
   pepper.with_llm("openai", api_key="your_key")
   ```

3. Initialize providers:
   ```python
   await pepper.initialize()
   ```

4. Use the providers:
   ```python
   response = await pepper.llm.chat(messages)
   ``` 