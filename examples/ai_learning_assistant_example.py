"""AI Learning Assistant Example.

This example demonstrates how to use PepperPy to create an AI-powered learning assistant
that provides personalized education through:
1. Contextual learning with RAG
2. Interactive conversations with LLM
3. Audio content generation with TTS
"""

import asyncio
from typing import Dict

from pepperpy import PepperPy


async def create_learning_assistant() -> PepperPy:
    """Create and configure the learning assistant."""
    return PepperPy().with_llm().with_rag().with_storage().with_tts()


async def load_student_knowledge(assistant: PepperPy, student_id: str) -> None:
    """Load student's learning materials and progress."""
    await assistant.learn([
        "Learning styles: Visual, Auditory, Reading/Writing, Kinesthetic",
        "Effective learning requires active engagement and practice",
        "Regular assessments help track progress and identify areas for improvement",
    ])

    await assistant.learn({
        "student_id": student_id,
        "learning_style": "visual",
        "current_level": "beginner",
        "interests": ["programming", "AI"],
        "completed_lessons": [],
    })


async def generate_lesson(assistant: PepperPy, topic: str) -> Dict:
    """Generate a personalized lesson."""
    result = await assistant.ask(
        f"Create a lesson about {topic} with: "
        "1. A brief introduction "
        "2. Key concepts "
        "3. An example or exercise"
    )

    lesson = {"topic": topic, "content": result.content}
    lesson["audio"] = await assistant.tts.convert_text(result.content)
    return lesson


async def assess_understanding(assistant: PepperPy, topic: str, answer: str) -> Dict:
    """Assess student's understanding of a topic."""
    result = await assistant.ask(
        f"Assess this answer about {topic}: {answer}\n\n"
        "Provide: \n"
        "1. A score out of 100\n"
        "2. What was done well\n"
        "3. Areas for improvement"
    )

    return {"feedback": result.content, "topic": topic, "answer": answer}


async def main() -> None:
    """Run the learning assistant example."""
    print("AI Learning Assistant Example")
    print("=" * 50)

    async with await create_learning_assistant() as assistant:
        await load_student_knowledge(assistant, "student123")

        print("\nGenerating a lesson about Python...")
        lesson = await generate_lesson(assistant, "Python basics")
        print(f"\nLesson content:\n{lesson['content']}")
        print("\nAudio version generated successfully")

        print("\nAssessing student's understanding...")
        assessment = await assess_understanding(
            assistant,
            "Python basics",
            "Python is a programming language that uses indentation and is good for beginners",
        )
        print(f"\nFeedback:\n{assessment['feedback']}")


if __name__ == "__main__":
    asyncio.run(main())
