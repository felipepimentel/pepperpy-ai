# LLM Interaction Workflow

A workflow plugin for interacting with Large Language Models (LLMs) providing an abstracted interface for:

1. Text completions
2. Chat conversations
3. Streaming responses
4. Text embeddings

## Features

- Text Completion: Generate text completions with various models
- Chat Interface: Create interactive chatbots with history management
- Streaming: Stream responses for better UX with real-time output
- Embeddings: Generate text embeddings for semantic search

## Configuration

The workflow can be configured with these options:

- `provider`: LLM provider to use (e.g., openai, anthropic, llama) (default: "openai")
- `model`: LLM model to use (default: "gpt-3.5-turbo")
- `api_key`: API key for the LLM provider (will use environment variable if not provided)
- `temperature`: Temperature for generation (0.0 to 1.0) (default: 0.7)
- `max_tokens`: Maximum tokens to generate (default: 1024)
- `streaming`: Whether to stream responses (default: false)
- `system_prompt`: System prompt for chat (default: "You are a helpful assistant...")
- `embedding_model`: Model for embeddings (default: "text-embedding-ada-002")
- `output_dir`: Directory to save results (default: "./output/llm")

## Usage

### Text Completion

```python
from pepperpy.workflow import create_provider

# Create the LLM interaction workflow provider
workflow = create_provider("llm_interaction", 
                          provider="openai",
                          model="gpt-4",
                          api_key="your_api_key")

# Execute a text completion
result = await workflow.execute({
    "task": "text_completion",
    "input": {
        "prompt": "Explain what PepperPy is in one paragraph."
    }
})

print(result["text"])
```

### Chat Interaction

```python
# Create workflow for chat
workflow = create_provider("llm_interaction", 
                          provider="openai",
                          model="gpt-3.5-turbo",
                          system_prompt="You are a helpful coding assistant.")

# Send messages
messages = [
    {"role": "user", "content": "How can I use Python's asyncio library?"}
]

result = await workflow.execute({
    "task": "chat",
    "input": {"messages": messages}
})

# Continue the conversation
messages.append({"role": "assistant", "content": result["text"]})
messages.append({"role": "user", "content": "Can you show me a simple example?"})

result = await workflow.execute({
    "task": "chat",
    "input": {"messages": messages}
})

print(result["text"])
```

### Streaming Chat

```python
# Create workflow with streaming enabled
workflow = create_provider("llm_interaction", 
                         provider="openai",
                         streaming=True)

# Stream chat response
result = await workflow.execute({
    "task": "stream_chat",
    "input": {
        "prompt": "Write a short story about a robot learning to cook."
    }
})

# The result contains the full response
print(f"Complete response: {result['text']}")
```

### Text Embeddings

```python
# Generate embeddings for semantic search
workflow = create_provider("llm_interaction", 
                          provider="openai",
                          embedding_model="text-embedding-ada-002")

# Get embeddings for multiple texts
result = await workflow.execute({
    "task": "embedding",
    "input": {
        "texts": [
            "What is artificial intelligence?",
            "Explain machine learning algorithms.",
            "How do neural networks work?"
        ],
        "output_file": "embeddings.json"  # Optional file to save embeddings
    }
})

# Access the embeddings
embeddings = result["embeddings"]
```

### Via CLI

```bash
# Run text completion via CLI
python -m pepperpy.cli workflow run workflow/llm_interaction \
  --params "provider=openai" \
  --params "task=text_completion" \
  --params "prompt=What is the capital of France?"

# Run streaming chat via CLI
python -m pepperpy.cli workflow run workflow/llm_interaction \
  --params "provider=openai" \
  --params "model=gpt-4" \
  --params "task=stream_chat" \
  --params "prompt=Tell me a short story" \
  --params "streaming=true"
```

## Requirements

- pydantic>=2.0.0
- jsonschema>=4.0.0
- numpy>=1.24.0
- tiktoken>=0.5.0

## API Keys

The workflow will look for environment variables with the format `{PROVIDER}_API_KEY` if not provided in the configuration. For example:

- `OPENAI_API_KEY` for OpenAI
- `ANTHROPIC_API_KEY` for Anthropic
- etc. 