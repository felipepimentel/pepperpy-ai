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


async def load_student_knowledge(pepper: PepperPy, student_id: str) -> None:
    """Load student's learning materials and progress."""
    # Load general learning principles
    await (
        pepper.chat.with_system("You are an education expert.")
        .with_user("""
            Learn and apply these educational principles:
            1. Learning styles: Visual, Auditory, Reading/Writing, Kinesthetic
            2. Effective learning requires active engagement and practice
            3. Regular assessments help track progress and identify areas for improvement
        """)
        .generate()
    )

    # Load student profile
    await (
        pepper.chat.with_system("You are a personalization expert.")
        .with_user(f"""
            Learn and apply this student profile:
            - Student ID: {student_id}
            - Learning style: visual
            - Current level: beginner
            - Interests: programming, AI
            - Completed lessons: []
        """)
        .generate()
    )


async def generate_lesson(pepper: PepperPy, topic: str) -> Dict:
    """Generate a personalized lesson.

    Args:
        pepper: Configured PepperPy instance
        topic: The lesson topic

    Returns:
        Dictionary containing the lesson content and audio
    """
    # Get lesson content
    result = await (
        pepper.chat.with_system("You are an expert teacher.")
        .with_user(
            f"Create a lesson about {topic} with: "
            "1. A brief introduction "
            "2. Key concepts "
            "3. An example or exercise"
        )
        .generate()
    )

    # Create the lesson dictionary with content
    content = result.content
    lesson = {"topic": topic, "content": content}

    # Generate audio version of the content
    audio = await pepper.tts.with_text(content).generate()

    lesson["audio_byte_size"] = str(len(audio.audio))
    return lesson


async def assess_understanding(pepper: PepperPy, topic: str, answer: str) -> Dict:
    """Assess student's understanding of a topic."""
    result = await (
        pepper.chat.with_system("You are an assessment expert.")
        .with_user(
            f"Assess this answer about {topic}: {answer}\n\n"
            "Provide: \n"
            "1. A score out of 100\n"
            "2. What was done well\n"
            "3. Areas for improvement"
        )
        .generate()
    )

    return {"feedback": result.content, "topic": topic, "answer": answer}


async def main() -> None:
    """Run the learning assistant example."""
    print("AI Learning Assistant Example")
    print("=" * 50)

    # Initialize PepperPy with LLM, RAG, and TTS support
    # Provider configuration comes from environment variables
    async with PepperPy().with_llm().with_rag().with_tts() as pepper:
        await load_student_knowledge(pepper, "student123")

        print("\nGenerating a lesson about Python...")
        lesson = await generate_lesson(pepper, "Python basics")
        print(f"\nLesson content:\n{lesson['content']}")
        print("\nAudio version generated successfully")

        print("\nAssessing student's understanding...")
        assessment = await assess_understanding(
            pepper,
            "Python basics",
            "Python is a programming language that uses indentation and is good for beginners",
        )
        print(f"\nFeedback:\n{assessment['feedback']}")


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_LLM__PROVIDER=openai
    # PEPPERPY_LLM__API_KEY=your_api_key
    # PEPPERPY_TTS__PROVIDER=azure
    # PEPPERPY_TTS__API_KEY=your_api_key
    # PEPPERPY_TTS__REGION=your_region
    # PEPPERPY_RAG__PROVIDER=memory
    asyncio.run(main())
