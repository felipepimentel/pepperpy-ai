"""
Example demonstrating in-memory RAG capabilities in PepperPy.

This example shows how to use the lightweight in-memory RAG provider
for simple retrieval augmented generation tasks, without requiring
any external dependencies or databases.
"""

import asyncio

from pepperpy import PepperPy


async def main() -> None:
    """Run the example."""
    print("In-Memory RAG Provider Example")
    print("==============================\n")

    # Initialize PepperPy with RAG and hash embeddings
    async with PepperPy().with_rag().with_embeddings() as pepper:
        # Add some documents
        await pepper.rag.add_documents([
            "The quick brown fox jumps over the lazy dog",
            "The lazy dog sleeps while the quick brown fox jumps",
            "The brown fox is quick and jumps high",
        ]).store()

        # Search the documents
        results = await pepper.rag.search("What does the fox do?").execute()
        print("Search results:", results)


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_RAG__PROVIDER=memory
    # PEPPERPY_EMBEDDINGS__PROVIDER=hash
    asyncio.run(main())
