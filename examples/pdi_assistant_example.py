"""Example of using PepperPy for a Personal Development Initiative (PDI) assistant."""

import asyncio
from typing import Any, Dict, List

from pepperpy import PepperPy


async def create_pdi(
    pepperpy: PepperPy,
    user_id: str,
    goals: List[str],
    action_plan: List[str],
    recommendations: List[str],
) -> Dict[str, Any]:
    """Create a PDI document.

    Args:
        pepperpy: PepperPy instance
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

    # Store PDI using learn method
    await pepperpy.learn(pdi)
    return pdi


async def main():
    # Initialize PepperPy with context manager and configure providers
    # Using lightweight providers by default for a minimal setup
    async with (
        PepperPy({
            "storage": {"provider": "local"},
            "rag": {"provider": "chroma"},
            "embeddings": {"provider": "numpy"},  # Using numpy embeddings by default
        })
        .with_embeddings()
        .with_rag()
        .with_storage()
    ) as pepperpy:
        # Create PDI
        pdi = await create_pdi(
            pepperpy=pepperpy,
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

        # Search PDIs using ask method
        result = await pepperpy.ask("What are the programming goals and action plan?")
        print("\nSearch results:")
        print(result.content)


if __name__ == "__main__":
    asyncio.run(main())
