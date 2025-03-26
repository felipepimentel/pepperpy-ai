"""Example of using PepperPy for a Personal Development Initiative (PDI) assistant."""

import asyncio
from typing import Any, Dict, List

from pepperpy import (
    Config,
    Document,
    PepperPy,
    RAGProvider,
    StorageProvider,
)


async def create_pdi(
    storage: StorageProvider,
    rag: RAGProvider,
    user_id: str,
    goals: List[str],
    action_plan: List[str],
    recommendations: List[str],
) -> Dict[str, Any]:
    """Create a PDI document.

    Args:
        storage: Storage provider
        rag: RAG provider
        user_id: User ID
        goals: List of goals
        action_plan: List of action plan steps
        recommendations: List of recommendations

    Returns:
        Created PDI document
    """
    # Create PDI document
    pdi = {
        "user_id": user_id,
        "goals": goals,
        "action_plan": action_plan,
        "recommendations": recommendations,
    }

    # Store PDI
    doc = Document(content=str(pdi))
    await storage.store_document("pdis", doc)
    await rag.add([doc])

    return pdi


async def main():
    # Configure providers
    config = Config({
        "storage": {"provider": "local"},
        "rag": {"provider": "annoy"},
        "embeddings": {"provider": "openai"},
    })

    # Initialize PepperPy
    async with PepperPy(config) as pepperpy:
        pepperpy.with_rag().with_storage()

        # Create PDI
        pdi = await create_pdi(
            storage=pepperpy.storage,
            rag=pepperpy.rag,
            user_id="user123",
            goals=[
                "Learn Python programming",
                "Exercise 3 times per week",
                "Read 2 books per month",
            ],
            action_plan=[
                "Break down Python learning into small modules",
                "Practice coding for 1 hour daily",
                "Build a small project each week",
            ],
            recommendations=[
                "Use online resources like Python.org",
                "Join a coding community",
                "Contribute to open source projects",
            ],
        )

        # Search PDIs
        results = await pepperpy.rag.search("programming goals")

        # Print results
        print("\nSearch results for 'programming goals':")
        for doc in results:
            pdi = eval(doc.content)  # Convert string back to dict
            print(f"\nUser: {pdi['user_id']}")
            print("Goals:", pdi["goals"])
            print("\nAction Plan:")
            for step in pdi["action_plan"]:
                print(f"- {step}")
            print("\nRecommendations:")
            for rec in pdi["recommendations"]:
                print(f"- {rec}")


if __name__ == "__main__":
    asyncio.run(main())
