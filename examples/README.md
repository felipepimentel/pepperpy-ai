# PepperPy Examples

This directory contains example applications demonstrating various features of the PepperPy framework.

## RAG with Memory Example

The `rag_memory_agent.py` example demonstrates:
1. Loading and processing PDF documents for knowledge base
2. Using RAG (Retrieval Augmented Generation) for context-aware responses
3. Maintaining conversation context with short-term memory
4. Storing and retrieving information from long-term memory
5. Fallback capabilities with multiple LLM providers

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Create .env file
cp .env.example .env

# Edit .env and add your API keys
PEPPERPY_API_KEY=your-openrouter-api-key
PEPPERPY_FALLBACK_API_KEY=your-fallback-api-key
```

3. Ensure you have the example PDF in place:
```bash
examples/resources/Newwhitepaper_Agents2.pdf
```

### Running the Example

```bash
python examples/rag_memory_agent.py
```

The example will:
1. Load and process the whitepaper PDF
2. Initialize conversation and memory systems
3. Run through a series of questions that demonstrate:
   - Knowledge retrieval from the PDF
   - Context awareness from conversation history
   - Memory retention and recall
4. Save conversation history and memories to files

### Output Files

The example generates:
- `conversation_history.json`: Complete conversation transcript
- `agent_memories.json`: Stored memories from the conversation

### Customization

You can modify:
- Questions in the `questions` list
- RAG parameters like chunk size and overlap
- Memory importance thresholds
- LLM provider configurations 