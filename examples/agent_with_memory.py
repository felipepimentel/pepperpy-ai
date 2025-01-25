"""Example demonstrating conversation, memory, and RAG features."""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

from pepperpy.providers.llm.huggingface import HuggingFaceProvider
from pepperpy.providers.llm.types import LLMConfig
from pepperpy.persistence.storage.conversation import Conversation, Message, MessageRole
from pepperpy.persistence.storage.memory import MemoryManager
from pepperpy.persistence.storage.rag import RAGManager
from pepperpy.persistence.storage.chunking import ChunkManager

async def main():
    # Load environment variables
    load_dotenv()

    # Check for required environment variables
    if not os.getenv("HUGGINGFACE_API_KEY"):
        raise ValueError("HUGGINGFACE_API_KEY environment variable is required")

    # Initialize LLM with HuggingFace provider
    llm_config = LLMConfig(
        api_key=os.environ["HUGGINGFACE_API_KEY"],
        model="gpt2",  # example model
        base_url="https://api-inference.huggingface.co/models"
    )
    
    llm = HuggingFaceProvider(llm_config.to_dict())

    try:
        # Initialize conversation
        conversation = Conversation()
        conversation.add_message(
            Message(
                role=MessageRole.SYSTEM,
                content="You are a helpful assistant with knowledge about the PepperPy library.",
                timestamp=datetime.now()
            )
        )

        # Initialize memory manager
        memory_manager = MemoryManager()

        # Initialize RAG manager
        rag_manager = RAGManager(
            llm=llm,
            chunk_manager=ChunkManager()
        )

        # Add document about PepperPy
        pepperpy_doc = """
        PepperPy is a Python framework for building AI agents with advanced conversation, memory, 
        and knowledge retrieval capabilities. It supports multiple LLM providers, has a flexible 
        memory system, and includes RAG functionality for enhanced responses.

        Key features include:
        1. Conversation Management: Track history and context
        2. Memory System: Short-term and long-term memory with importance scoring
        3. RAG System: Document chunking and semantic search
        4. LLM Provider Management: Multiple providers with fallback support

        The library is designed to be modular and extensible, making it easy to add new 
        capabilities or integrate with other frameworks.
        """
        await rag_manager.add_document(
            content=pepperpy_doc,
            doc_id="pepperpy_overview",
            metadata={"type": "documentation", "section": "overview"}
        )

        # Simulate a conversation about PepperPy
        questions = [
            "What is PepperPy?",
            "How does the memory system work?",
            "Can you explain the RAG functionality?",
            "What LLM providers are supported?"
        ]

        for question in questions:
            # Add user question to conversation
            conversation.add_message(
                Message(
                    role=MessageRole.USER,
                    content=question,
                    timestamp=datetime.now()
                )
            )

            # Generate response using RAG
            response = await rag_manager.generate_with_context(
                query=question,
                conversation=conversation,
                prompt_template=(
                    "Based on the following context and conversation history, "
                    "provide a detailed answer to the question.\n\n"
                    "Context:\n{context}\n\n"
                    "Conversation History:\n{history}\n\n"
                    "Question: {query}\n\n"
                    "Answer:"
                )
            )

            # Add assistant response to conversation
            conversation.add_message(
                Message(
                    role=MessageRole.ASSISTANT,
                    content=response.text,
                    timestamp=datetime.now()
                )
            )

            # Store response in memory
            await memory_manager.add_memory(
                content=response.text,
                importance=0.8,
                metadata={
                    "type": "response",
                    "question": question,
                    "tokens": response.tokens_used,
                    "cost": response.cost
                }
            )

            print(f"\nQ: {question}")
            print(f"A: {response.text}\n")

        # Save conversation history
        conversation.save_to_json("conversation.json")

        # Save memories
        await memory_manager.save_memories("memories.json")

        # Save RAG documents
        await rag_manager.save_documents("documents.json")

    finally:
        # Cleanup
        await memory_manager.cleanup()
        await rag_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 