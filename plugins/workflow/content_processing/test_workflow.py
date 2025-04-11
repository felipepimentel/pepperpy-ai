"""Simple test script for content processing workflow."""

import asyncio
import os
import tempfile
from pathlib import Path


async def process_text(text: str) -> dict:
    """Process text content using simple NLP techniques.

    Args:
        text: Text to process

    Returns:
        Processing results
    """
    # Basic text processing
    words = text.split()
    sentences = [s.strip() for s in text.split(".") if s.strip()]

    # Calculate basic metrics
    word_count = len(words)
    sentence_count = len(sentences)
    avg_sentence_length = word_count / max(sentence_count, 1)

    # Get most common words
    from collections import Counter

    word_freq = Counter(word.lower().strip(".,!?;:()[]{}\"'") for word in words)
    common_words = word_freq.most_common(5)

    return {
        "metrics": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": avg_sentence_length,
        },
        "common_words": common_words,
        "sample": text[:100] + ("..." if len(text) > 100 else ""),
    }


async def process_document(file_path: str) -> dict:
    """Process a document file.

    Args:
        file_path: Path to document

    Returns:
        Processing results
    """
    # Check if file exists
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    # Read file content
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()

        # Process the content
        processing_result = await process_text(content)

        # Add file metadata
        file_info = {
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "extension": path.suffix,
        }

        return {
            "status": "success",
            "file_info": file_info,
            "content_analysis": processing_result,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


async def create_test_file() -> str:
    """Create a test file with sample content.

    Returns:
        Path to test file
    """
    # Sample text for processing
    sample_text = """
    PepperPy is a unified abstraction for AI/LLM ecosystems with a focus on agentic AI capabilities.
    It is not just a wrapper for LLMs or RAG, but a comprehensive agentic platform.
    The framework facilitates orchestration of autonomous agents and workflows.
    PepperPy is designed to be composable, with independent components that can be combined.
    The architecture follows a "think vertical, not horizontal" approach, organized by business domains rather than technical types.
    """

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as temp:
        temp.write(sample_text)
        return temp.name


async def main():
    """Run content processing tests."""
    print("\n🔍 CONTENT PROCESSING WORKFLOW TEST\n")

    # Create a test file
    test_file = await create_test_file()
    print(f"Created test file: {test_file}")

    try:
        # Process text directly
        sample_text = "The PepperPy framework provides a unified abstraction for AI and LLM ecosystems. It focuses on agentic capabilities and workflow orchestration."
        print("\n📝 Processing text sample...")
        text_result = await process_text(sample_text)

        # Display text processing results
        print("\n📊 Text processing results:")
        print(f"  Sample: {text_result['sample']}")
        print(f"  Words: {text_result['metrics']['word_count']}")
        print(f"  Sentences: {text_result['metrics']['sentence_count']}")
        print(
            f"  Avg sentence length: {text_result['metrics']['avg_sentence_length']:.2f} words"
        )
        print("\n  Most common words:")
        for word, count in text_result["common_words"]:
            print(f"    - {word}: {count}")

        # Process the test file
        print("\n📄 Processing test file...")
        file_result = await process_document(test_file)

        # Display file processing results
        if file_result.get("status") == "success":
            print("\n✅ File processing successful!")
            print("\n📄 File information:")
            file_info = file_result["file_info"]
            for key, value in file_info.items():
                print(f"  {key}: {value}")

            print("\n📊 Content analysis:")
            content = file_result["content_analysis"]
            print(f"  Words: {content['metrics']['word_count']}")
            print(f"  Sentences: {content['metrics']['sentence_count']}")
            print(
                f"  Avg sentence length: {content['metrics']['avg_sentence_length']:.2f} words"
            )
        else:
            print(
                f"\n❌ File processing failed: {file_result.get('error', 'Unknown error')}"
            )

    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"\nRemoved test file: {test_file}")


if __name__ == "__main__":
    asyncio.run(main())
