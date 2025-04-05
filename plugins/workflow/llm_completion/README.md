# LLM Completion Workflow

A simple workflow plugin for generating text with Large Language Models:

1. Text completion with various prompts
2. Content generation with custom system instructions
3. Completion with basic formatting options

## Features

- Text Completion: Generate completions with various models
- Content Generation: Create various types of content with different instructions
- Format Control: Control output format with system instructions

## Configuration

The workflow can be configured with these options:

- `provider`: LLM provider to use (default: "openai")
- `model`: LLM model to use (default: "gpt-3.5-turbo")
- `api_key`: API key for the LLM provider
- `temperature`: Temperature for generation (0.0 to 1.0) (default: 0.7)
- `max_tokens`: Maximum tokens to generate (default: 1024)
- `system_prompt`: System prompt for completions (default: "You are a helpful assistant...")
- `output_dir`: Directory to save results (default: "./output/llm")

## Usage

### Basic Text Completion

```python
from pepperpy.workflow import create_provider

# Create the LLM completion workflow provider
workflow = create_provider("llm_completion", 
                         provider="openai",
                         model="gpt-4",
                         api_key="your_api_key")

# Generate a completion
result = await workflow.execute({
    "task": "complete",
    "input": {
        "prompt": "Explain what PepperPy is in one paragraph."
    }
})

print(result["text"])
```

### Content Generation

```python
# Create workflow with custom system prompt
workflow = create_provider("llm_completion", 
                         provider="openai",
                         model="gpt-3.5-turbo",
                         system_prompt="You are a creative writer who specializes in short stories.")

# Generate a short story
result = await workflow.execute({
    "task": "complete",
    "input": {
        "prompt": "Write a short story about a robot learning to cook."
    }
})

print(result["text"])
```

### Format Control

```python
# Control output format with system instruction
workflow = create_provider("llm_completion", 
                         provider="openai",
                         model="gpt-3.5-turbo")

# Generate in specific output format
result = await workflow.execute({
    "task": "complete",
    "input": {
        "prompt": "List 5 best practices for Python development.",
        "system_prompt": "You output lists in markdown format with detailed explanations."
    }
})

# Get formatted output
print(result["text"])
```

### Via CLI

```bash
# Run completion via CLI
python -m pepperpy.cli workflow run workflow/llm_completion \
  --params "provider=openai" \
  --params "model=gpt-4" \
  --params "task=complete" \
  --params "prompt=What is the capital of France?"

# Generate with custom system prompt
python -m pepperpy.cli workflow run workflow/llm_completion \
  --params "provider=openai" \
  --params "task=complete" \
  --params "prompt=Write a poem about AI" \
  --params "system_prompt=You are a famous poet who writes short, powerful poems"
```

## Requirements

- pydantic>=2.0.0
- jsonschema>=4.0.0
- tiktoken>=0.5.0

## API Keys

The workflow will look for environment variables with the format `{PROVIDER}_API_KEY` if not provided in the configuration. For example:

- `OPENAI_API_KEY` for OpenAI
- `ANTHROPIC_API_KEY` for Anthropic
- etc. 