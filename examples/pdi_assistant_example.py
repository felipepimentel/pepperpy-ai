"""Example of using PepperPy for PDI assistance."""

import asyncio

import pepperpy

# Sample PDI data
pdi = {
    "name": "John Doe",
    "age": 30,
    "occupation": "Software Engineer",
    "skills": ["Python", "JavaScript", "Docker"],
    "experience": [
        {
            "company": "Tech Corp",
            "role": "Senior Developer",
            "duration": "2 years",
            "achievements": [
                "Led team of 5 developers",
                "Improved system performance by 40%",
            ],
        },
        {
            "company": "Startup Inc",
            "role": "Full Stack Developer",
            "duration": "3 years",
            "achievements": [
                "Developed e-commerce platform",
                "Implemented CI/CD pipeline",
            ],
        },
    ],
}


async def main() -> None:
    """Run the example."""
    # Initialize PepperPy with fluent API
    # All configuration comes from environment variables (.env file)
    pepperpy_instance = (
        pepperpy.PepperPy()
        .with_llm()  # Uses PEPPERPY_LLM__PROVIDER and other env vars
        .with_embeddings()  # Uses PEPPERPY_EMBEDDINGS__PROVIDER and other env vars
        .with_rag()  # Uses PEPPERPY_RAG__PROVIDER and other env vars
    )

    # Use async context manager to automatically initialize and cleanup
    async with pepperpy_instance:
        # Learn from PDI data
        await pepperpy_instance.learn(pdi)

        # Ask questions about the PDI
        questions = [
            "What is John's current occupation?",
            "What are his key skills?",
            "How many years of experience does he have?",
            "What were his main achievements at Tech Corp?",
        ]

        for question in questions:
            print(f"\nQuestion: {question}")
            response = await pepperpy_instance.ask(question)
            print(f"Answer: {response}")


if __name__ == "__main__":
    asyncio.run(main())
