# Pepperpy Prompts

This directory contains prompt templates used throughout the Pepperpy system. The prompts are organized by category and follow a standardized YAML format for consistency and maintainability.

## Directory Structure

```plaintext
prompts/
├── agents/              # Agent-specific prompts
│   ├── reasoning/       # Reasoning prompts (ReAct, CoT, etc)
│   ├── memory/         # Memory management prompts
│   └── orchestration/  # Multi-agent coordination
├── providers/          # Provider-specific prompts
│   ├── openai/        # OpenAI-specific prompts
│   └── anthropic/     # Anthropic-specific prompts
├── tools/             # Tool-specific prompts
│   ├── code/          # Code generation/analysis
│   ├── data/          # Data processing
│   └── search/        # Search and retrieval
└── templates/         # Reusable prompt templates
```

## Prompt Format

Each prompt is defined in YAML format with the following structure:

```yaml
metadata:
  name: "prompt_name"
  version: "1.0"
  category: "category/subcategory"
  model: "model_name"
  temperature: 0.7
  tags: ["tag1", "tag2"]

context:
  description: "Purpose and context"
  input_format: "Expected input format"
  output_format: "Expected output format"
  examples:
    - input: "Example input"
      output: "Example output"

template: |
  The actual prompt template with
  {{variables}} for substitution

validation:
  required_fields: ["field1", "field2"]
  constraints:
    max_length: 2000
    required_sections: ["section1", "section2"]
```

## Usage

Prompts can be loaded and used with the `PromptTemplate` class:

```python
from pepperpy.prompts import PromptTemplate
from pepperpy.common.config import get_config

# Load a prompt template
prompt = PromptTemplate.load(
    "agents/reasoning/react.yaml",
    model="gpt-4",  # Optional override
    temperature=0.7  # Optional override
)

# Format and execute with a provider
response = await prompt.execute(
    provider,
    goal="Analyze code performance",
    tools=["profiler", "analyzer"]
)
```

## Best Practices

1. **Modularity**
   - Break prompts into reusable components
   - Use template variables for customization
   - Maintain single responsibility

2. **Versioning**
   - Track prompt versions
   - Document changes
   - Maintain backward compatibility

3. **Testing**
   - Include example inputs/outputs
   - Validate prompt effectiveness
   - Measure performance metrics

4. **Documentation**
   - Clear purpose and usage
   - Input/output specifications
   - Known limitations

## Development

When creating new prompts:

1. Choose appropriate category
2. Follow YAML format
3. Include comprehensive examples
4. Add validation rules
5. Test with different inputs
6. Document usage and limitations

## Monitoring

Monitor prompt performance:

1. **Usage Tracking**
   - Prompt utilization
   - Success rates
   - Performance metrics

2. **Quality Control**
   - Output validation
   - Error analysis
   - Improvement tracking

3. **Cost Management**
   - Token usage
   - API costs
   - Optimization opportunities 