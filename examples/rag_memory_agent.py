"""Example demonstrating RAG with memory capabilities."""

import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv

from pepperpy.providers.llm.manager import LLMManager
from pepperpy.providers.memory.memory_store import MemoryEntry, LongTermMemory
from pepperpy.capabilities.tools.document_loader import DocumentLoaderTool

async def main():
    """Run the RAG with memory example."""
    # Load environment variables
    load_dotenv()

    # Get API keys from environment
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise ValueError("HUGGINGFACE_API_KEY environment variable is required")

    # Initialize LLM manager with multiple providers
    llm_manager = LLMManager()
    await llm_manager.initialize({
        "primary": {
            "api_key": api_key,
            "model": "mistralai/Mistral-7B-Instruct-v0.1",
            "base_url": "https://api-inference.huggingface.co/models",
            "temperature": 0.7,
            "max_tokens": 1000,
            "is_fallback": False,
            "priority": 1
        },
        "fallback1": {
            "api_key": api_key,
            "model": "HuggingFaceH4/zephyr-7b-beta",
            "base_url": "https://api-inference.huggingface.co/models",
            "temperature": 0.7,
            "max_tokens": 1000,
            "is_fallback": True,
            "priority": 2
        }
    })

    try:
        # Initialize memory manager
        memory_manager = LongTermMemory(storage_path="memories.json")

        # Initialize document loader
        document_loader = DocumentLoaderTool()
        await document_loader.initialize()

        print("\nLoading whitepaper...")
        doc_result = await document_loader.execute(
            path="examples/resources/Newwhitepaper_Agents2.pdf"
        )
        
        if not doc_result.success or not doc_result.data:
            raise Exception(f"Failed to load document: {doc_result.error}")

        document = doc_result.data
        if not document.content:
            raise Exception("Document content is empty")

        print("Document loaded successfully!")
        print(f"Content length: {len(document.content)} characters")

        # Example questions to demonstrate memory and context
        questions = [
            "What are the main types of agent architectures discussed in the whitepaper?",
            "Based on our previous discussion about agent architectures, which one would be best for a personal assistant?",
            "Can you explain how the memory system works in these agents, considering what we discussed about architectures?",
        ]

        print("\nStarting conversation...\n")

        for i, question in enumerate(questions, 1):
            print(f"\nQ{i}: {question}")
            
            try:
                # Generate response using LLM with document context
                response = await llm_manager.get_primary_provider().generate(
                    prompt=(
                        "You are a knowledgeable assistant that helps users understand "
                        "agent architectures and AI systems. Use the following document "
                        "content to answer the question.\n\n"
                        f"Document content:\n{document.content[:2000]}...\n\n"
                        f"Question: {question}\n\n"
                        "Answer:"
                    )
                )
            except Exception as e:
                print(f"\nError with primary provider: {e}")
                print("Trying fallback provider...")
                try:
                    fallback_providers = llm_manager.get_fallback_providers()
                    if not fallback_providers:
                        raise Exception("No fallback providers available")
                    
                    response = await fallback_providers[0].generate(
                        prompt=(
                            "You are a knowledgeable assistant that helps users understand "
                            "agent architectures and AI systems. Use the following document "
                            "content to answer the question.\n\n"
                            f"Document content:\n{document.content[:2000]}...\n\n"
                            f"Question: {question}\n\n"
                            "Answer:"
                        )
                    )
                except Exception as e:
                    print(f"Error with fallback provider: {e}")
                    response = "I apologize, but I encountered an error while trying to generate a response. Please try again."

            # Store important information in memory
            await memory_manager.add_memory(
                MemoryEntry(
                    content=response,
                    importance=0.9,
                    metadata={
                        "type": "response",
                        "question": question,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            )

            print(f"A: {response}\n")

            # Query memory to demonstrate retention
            if i > 1:
                print("\nRelevant memories:")
                memories = await memory_manager.get_relevant_memories(
                    query=question,
                    limit=2
                )
                for memory, score in memories:
                    print(f"- [{score:.2f}] {memory.content[:200]}...")

        # Save memories
        memory_manager._save_memories()  # Note: Using internal method as it's what's available
        print("\nMemories saved to memories.json")

    finally:
        # Cleanup
        await llm_manager.cleanup()
        await memory_manager.clear()  # Use clear instead of cleanup
        await document_loader.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 