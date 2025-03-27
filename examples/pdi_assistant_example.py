"""Example of using PepperPy for PDI assistance."""

import asyncio
import logging

import pepperpy
from pepperpy.embeddings.providers.local import LocalProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    # Create embedding provider
    embedding_provider = LocalProvider()

    # Initialize PepperPy with all required providers
    pepperpy_instance = (
        pepperpy.PepperPy()
        .with_llm()  # Will use PEPPERPY_LLM__PROVIDER and PEPPERPY_LLM__OPENAI__API_KEY from .env
        .with_embeddings(provider=embedding_provider)
        .with_rag(provider_type="chroma", embedding_provider=embedding_provider)
    )

    # Initialize all providers
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
            logger.info("\nQuestion: %s", question)
            response = await pepperpy_instance.ask(question)
            logger.info("Answer: %s", response)


if __name__ == "__main__":
    asyncio.run(main())
