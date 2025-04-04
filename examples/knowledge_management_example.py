#!/usr/bin/env python3
"""
Knowledge Management Example

This example demonstrates PepperPy's declarative API for knowledge management:
1. Creating and querying knowledge bases
2. Using RAG for improved responses
3. Working with conversation memory
"""

import asyncio
from pathlib import Path

from pepperpy import PepperPy

# Define output directory
OUTPUT_DIR = Path(__file__).parent / "output" / "knowledge"

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

# Sample conversation for memory demonstration
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


async def main():
    """Demonstrate knowledge management using PepperPy's declarative API."""
    # Setup pipeline with configuration
    pepper = PepperPy().configure(
        output_dir=OUTPUT_DIR,
        log_level="INFO",
        log_to_console=True,
        auto_save_results=True,
    )

    # Create a knowledge base with our documents
    kb = (
        pepper.knowledge_base("ai_concepts")
        .add_documents(DOCUMENTS)
        .configure(
            chunk_size=1000,
            embedding_model="text-embedding-ada-002",
            vector_store="chroma",
        )
    )

    # Define all knowledge tasks declaratively
    tasks = [
        # Basic knowledge base query
        pepper.knowledge_task("rag_query")
        .prompt("What is RAG and how does it work?")
        .using(kb)
        .output("rag_answer.txt"),
        # RAG-enhanced explanation
        pepper.knowledge_task("rag_explanation")
        .prompt("Explain how RAG systems improve the accuracy of LLMs")
        .using(kb)
        .parameters({"detail_level": "high"})
        .output("rag_explanation.txt"),
        # Memory-based task
        pepper.conversation_task("memory_response")
        .prompt(
            "Based on what we discussed earlier, can you explain how retrieval works in language models?"
        )
        .history(SAMPLE_CONVERSATION)
        .conversation_id("memory-example")
        .output("memory_response.txt"),
        # Combined knowledge + memory task
        pepper.knowledge_task("advanced_retrieval")
        .prompt("Compare different vector embedding approaches for retrieval systems")
        .using(kb)
        .with_history(SAMPLE_CONVERSATION)
        .parameters({"format": "comparison"})
        .output("advanced_retrieval.txt"),
    ]

    # Execute all knowledge tasks - potentially in parallel
    await pepper.run_knowledge_tasks(tasks)

    # Additional option: Conversational interface
    chat_session = pepper.chat_session("kb_chat").using(kb)
    # Add tasks to chat pipeline
    for task in tasks:
        chat_session.add_task(task)

    # Execute interactive session (commented out for demonstration)
    # await chat_session.start()

    # Display results
    print("\nAll knowledge management tasks completed successfully!")
    print(f"Results saved to {OUTPUT_DIR}")
    for task in tasks:
        print(f"- {task.name}: Task completed")


if __name__ == "__main__":
    asyncio.run(main())
