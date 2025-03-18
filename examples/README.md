# PepperPy Examples

This directory contains example scripts demonstrating various features and use cases of the PepperPy framework.

## Structure

- `basic/`: Basic examples showing core functionality
  - `pipeline_composition.py`: How to compose and execute pipelines
  - `intent_recognition.py`: Working with intent recognition
  - `transform_registry.py`: Using the transform registry

- `advanced/`: More complex examples
  - `rag_pipeline.py`: Building a RAG (Retrieval Augmented Generation) pipeline
  - `workflow_management.py`: Managing complex workflows
  - `caching_strategies.py`: Implementing caching strategies

- `integrations/`: Examples of integrating with other tools/services
  - `openai_integration.py`: Using OpenAI with PepperPy
  - `langchain_integration.py`: Integrating with LangChain
  - `huggingface_integration.py`: Working with Hugging Face models

## Running the Examples

1. Install PepperPy with all optional dependencies:
   ```bash
   pip install pepperpy[all]
   ```

2. Set up environment variables (if needed):
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configurations
   ```

3. Run an example:
   ```bash
   python examples/basic/pipeline_composition.py
   ```

## Contributing

Feel free to contribute your own examples! Please follow these guidelines:
- Include clear documentation and comments
- Add any required dependencies to `pyproject.toml`
- Update this README.md with your example's description
- Ensure the example follows our coding standards

## License

All examples are licensed under the MIT License. See the LICENSE file in the root directory for details. 