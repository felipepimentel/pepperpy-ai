"""Example script demonstrating text chunking strategies."""

import asyncio
from pepperpy.rag.chunking.base import ChunkingOptions
from pepperpy.rag.chunking.semantic import SemanticChunker
from pepperpy.rag.chunking.recursive import RecursiveCharNGramChunker
from pepperpy.rag.chunking.transformers import SentenceTransformersChunker


async def semantic_chunking() -> None:
    """Demonstrate semantic chunking using SpaCy."""
    print("\n=== Semantic Chunking ===")
    
    text = """
    Natural language processing (NLP) is a field of artificial intelligence 
    that focuses on the interaction between computers and human language.
    
    Machine learning algorithms are used to process and analyze large amounts
    of natural language data. This enables computers to understand the meaning
    of text and speech.
    
    Deep learning models have revolutionized NLP by achieving state-of-the-art
    results on many language tasks. These models can learn complex patterns
    in language data automatically.
    """
    
    chunker = SemanticChunker()
    options = ChunkingOptions(
        chunk_size=100,
        chunk_overlap=20,
        min_chunk_size=50,
        max_chunk_size=150
    )
    
    try:
        # Initialize chunker
        await chunker.initialize()
        
        # Split text into chunks
        chunks = await chunker.chunk_text(text, options)
        
        print(f"\nSplit into {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i}:")
            print(f"Text: {chunk.text}")
            print(f"Start: {chunk.start}, End: {chunk.end}")
            print(f"Length: {len(chunk.text)}")
            print(f"Metadata: {chunk.metadata}")
            
        # Merge chunks back
        merged = await chunker.merge_chunks(chunks)
        print(f"\nMerged text length: {len(merged)}")
        
    finally:
        await chunker.cleanup()


async def recursive_chunking() -> None:
    """Demonstrate recursive character n-gram chunking."""
    print("\n=== Recursive Chunking ===")
    
    text = """
    Text chunking is the process of splitting large documents into smaller,
    manageable pieces while preserving meaning and context.
    
    Different chunking strategies can be used depending on the requirements:
    - Fixed-size chunks with overlap
    - Semantic boundaries like sentences and paragraphs
    - Dynamic sizing based on content
    
    The choice of chunking strategy affects downstream tasks like:
    1. Document indexing
    2. Search relevance
    3. Question answering
    4. Text summarization
    """
    
    chunker = RecursiveCharNGramChunker()
    options = ChunkingOptions(
        chunk_size=120,
        chunk_overlap=30,
        min_chunk_size=60,
        max_chunk_size=180
    )
    
    try:
        # Initialize chunker
        await chunker.initialize()
        
        # Split text into chunks
        chunks = await chunker.chunk_text(text, options)
        
        print(f"\nSplit into {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i}:")
            print(f"Text: {chunk.text}")
            print(f"Start: {chunk.start}, End: {chunk.end}")
            print(f"Length: {len(chunk.text)}")
            print(f"Metadata: {chunk.metadata}")
            
        # Merge chunks back
        merged = await chunker.merge_chunks(chunks)
        print(f"\nMerged text length: {len(merged)}")
        
    finally:
        await chunker.cleanup()


async def transformer_chunking() -> None:
    """Demonstrate sentence transformer chunking."""
    print("\n=== Transformer Chunking ===")
    
    text = """
    Transformers have revolutionized natural language processing by enabling
    better understanding of context and meaning in text.
    
    The attention mechanism allows models to focus on relevant parts of the
    input when making predictions. This has led to significant improvements
    in many NLP tasks.
    
    Pre-trained language models can be fine-tuned for specific tasks like:
    - Text classification
    - Named entity recognition
    - Question answering
    - Machine translation
    
    Transfer learning from these pre-trained models has made it possible to
    achieve good results with less task-specific training data.
    """
    
    chunker = SentenceTransformersChunker()
    options = ChunkingOptions(
        chunk_size=150,
        chunk_overlap=40,
        min_chunk_size=80,
        max_chunk_size=200
    )
    
    try:
        # Initialize chunker
        await chunker.initialize()
        
        # Split text into chunks
        chunks = await chunker.chunk_text(text, options)
        
        print(f"\nSplit into {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i}:")
            print(f"Text: {chunk.text}")
            print(f"Start: {chunk.start}, End: {chunk.end}")
            print(f"Length: {len(chunk.text)}")
            print(f"Metadata: {chunk.metadata}")
            
        # Merge chunks back
        merged = await chunker.merge_chunks(chunks)
        print(f"\nMerged text length: {len(merged)}")
        
    finally:
        await chunker.cleanup()


async def main() -> None:
    """Run chunking examples."""
    await semantic_chunking()
    await recursive_chunking()
    await transformer_chunking()


if __name__ == "__main__":
    asyncio.run(main()) 