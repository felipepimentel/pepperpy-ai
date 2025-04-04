#!/usr/bin/env python3
"""
Knowledge Management Example

This example demonstrates PepperPy's knowledge management capabilities for:
1. Creating and querying knowledge bases
2. Using RAG for improved responses
3. Working with conversation memory
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Output directory
OUTPUT_DIR = Path(__file__).parent / "output" / "knowledge"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sample documents - PepperPy handles parsing and processing internally
DOCUMENTS = [
    """
    # Large Language Models (LLMs)
    
    Large Language Models (LLMs) are sophisticated AI systems trained on vast amounts of text data. 
    They can generate human-like text, translate languages, answer questions, and perform various 
    language-related tasks with remarkable accuracy.
    
    ## Training Process
    
    LLMs are typically trained in two phases:
    
    1. **Pre-training**: The model learns from a vast corpus of text data to predict the next word 
       in a sequence, developing a statistical understanding of language patterns.
    
    2. **Fine-tuning**: The pre-trained model is further refined on specific tasks or domains to 
       enhance its capabilities for particular applications.
    
    ## Key Capabilities
    
    Modern LLMs can:
    - Generate coherent and contextually relevant text
    - Answer questions based on learned knowledge
    - Summarize long documents
    - Translate between languages
    - Write creative content like stories or poems
    - Assist with coding tasks
    """,
    """
    # Retrieval Augmented Generation (RAG)
    
    Retrieval Augmented Generation (RAG) is an AI framework that combines the strengths of 
    retrieval-based systems with generative models to produce more accurate and informative responses.
    
    ## How RAG Works
    
    RAG operates in three main steps:
    
    1. **Retrieval**: When a query is received, the system searches through a knowledge base to find 
       relevant documents or passages.
    
    2. **Augmentation**: The retrieved information is added to the prompt sent to the language model,
       providing context and factual grounding.
    
    3. **Generation**: The language model generates a response based on both its parametric knowledge
       and the retrieved information.
    
    ## Benefits of RAG
    
    RAG offers several advantages over traditional approaches:
    
    - **Improved Accuracy**: By grounding responses in retrieved information, RAG reduces hallucinations
      and factual errors.
    
    - **Knowledge Recency**: The knowledge base can be updated without retraining the entire model,
      allowing for up-to-date information.
    
    - **Transparency**: Retrieved passages can be cited as sources, making the system more explainable.
    
    - **Efficiency**: RAG can work with smaller language models since not all knowledge needs to be
      stored in the model's parameters.
    """,
    """
    # Embeddings in Machine Learning
    
    Embeddings are dense vector representations of data that capture semantic meaning in a way that 
    machines can understand and process. They are crucial for many natural language processing and 
    machine learning tasks.
    
    ## Vector Embeddings
    
    Vector embeddings map discrete objects (like words, sentences, or documents) to continuous vector 
    spaces, where:
    
    - Similar items are positioned close together
    - Relationships between items are preserved as geometric relationships
    - Mathematical operations can reveal semantic connections
    
    ## Types of Embeddings
    
    Different types of embeddings are used for various applications:
    
    - **Word Embeddings**: Represent individual words (e.g., Word2Vec, GloVe)
    - **Sentence Embeddings**: Capture meaning at the sentence level
    - **Document Embeddings**: Represent entire documents or passages
    - **Cross-modal Embeddings**: Connect different types of data (e.g., text and images)
    
    ## Applications
    
    Embeddings enable various applications:
    
    - **Semantic Search**: Finding information based on meaning rather than keywords
    - **Recommendation Systems**: Suggesting related items based on embedding similarity
    - **Classification**: Categorizing text based on its embedded representation
    - **Clustering**: Grouping similar items together
    - **Transfer Learning**: Leveraging pre-trained embeddings for downstream tasks
    """,
]

# Sample conversation - PepperPy handles conversation state internally
SAMPLE_CONVERSATION = [
    {"role": "user", "content": "I want to learn about large language models."},
    {
        "role": "assistant",
        "content": "Large Language Models (LLMs) are sophisticated AI systems trained on vast amounts of text data. They can generate human-like text, translate languages, answer questions, and perform various language-related tasks with remarkable accuracy. Would you like to know more about how they're trained, their capabilities, or their applications?",
    },
    {"role": "user", "content": "Yes, please tell me about their training process."},
    {
        "role": "assistant",
        "content": "LLMs are typically trained in two main phases:\n\n1. **Pre-training**: The model learns from a vast corpus of text data to predict the next word in a sequence, developing a statistical understanding of language patterns. This phase requires enormous computational resources and large datasets.\n\n2. **Fine-tuning**: After pre-training, the model is refined on specific tasks or domains to enhance its capabilities for particular applications. This involves training on more focused datasets with human feedback.\n\nSome models also undergo reinforcement learning from human feedback (RLHF), where human preferences are used to further improve the model's outputs. This helps align the model's behavior with human values and expectations.",
    },
    {"role": "user", "content": "How do these models handle knowledge retrieval?"},
]


async def knowledge_base_example() -> None:
    """Demonstrate knowledge management capabilities."""
    # PepperPy handles embeddings, vector storage, logging, and saving results
    async with PepperPy().with_llm().with_rag() as pepper:
        # Setup context with our documents
        knowledge_context = {
            "documents": DOCUMENTS,
            "topic": "AI concepts and techniques",
        }

        # Execute query with RAG-enhanced context
        await pepper.execute(
            "What is RAG and how does it work?",
            context=knowledge_context,
            output_path=OUTPUT_DIR / "rag_answer.txt",
            metadata={"query": "What is RAG and how does it work?"},
        )


async def rag_conversation_example() -> None:
    """Demonstrate RAG-enhanced conversation."""
    # PepperPy handles RAG, logging, and result storage
    async with PepperPy().with_llm().with_rag() as pepper:
        # Execute query with knowledge grounding
        await pepper.execute(
            "Explain how RAG systems improve the accuracy of LLMs",
            context={"documents": DOCUMENTS},
            output_path=OUTPUT_DIR / "rag_explanation.txt",
            metadata={
                "question": "Explain how RAG systems improve the accuracy of LLMs"
            },
        )


async def memory_example() -> None:
    """Demonstrate conversation memory capabilities."""
    # PepperPy handles conversation memory, logging, and result saving
    async with PepperPy().with_llm() as pepper:
        # Execute with conversation history context
        await pepper.execute(
            "Based on what we discussed earlier, can you explain how retrieval works in language models?",
            context={"conversation_history": SAMPLE_CONVERSATION},
            output_path=OUTPUT_DIR / "memory_response.txt",
            conversation_id="memory-example",
        )


async def main() -> None:
    """Run all knowledge management examples."""
    # PepperPy should handle both console output and logging
    pepper = PepperPy()

    # Initialize with logging and output configuration
    await pepper.initialize(
        output_dir=OUTPUT_DIR, log_level="INFO", log_to_console=True, log_to_file=True
    )

    await pepper.log_header("PEPPERPY KNOWLEDGE MANAGEMENT EXAMPLE")

    await knowledge_base_example()
    await rag_conversation_example()
    await memory_example()

    # Finalize with automatic summary of results
    await pepper.finalize(
        summary_message="All knowledge management examples completed!",
        output_dir=OUTPUT_DIR,
    )


if __name__ == "__main__":
    asyncio.run(main())
