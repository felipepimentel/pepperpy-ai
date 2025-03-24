"""AI Learning Assistant Example.

This example demonstrates a comprehensive learning assistant that:
1. Uses multiple specialized agents for different aspects of learning
2. Maintains context of student's progress using RAG
3. Generates personalized learning materials
4. Creates interactive quizzes and exercises
5. Provides detailed explanations and feedback
6. Integrates with educational APIs and resources
"""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from pepperpy.agents import create_agent_group, execute_task, cleanup_group
from pepperpy.agents.provider import Message
from pepperpy.rag import Document, Query
from pepperpy.rag.providers import SupabaseRAGProvider
from pepperpy.tts import convert_text, save_audio


@dataclass
class LearningProgress:
    """Tracks a student's learning progress."""
    
    student_id: str
    topic: str
    start_date: datetime
    current_level: int
    completed_lessons: List[str]
    quiz_scores: Dict[str, float]
    strengths: List[str]
    areas_for_improvement: List[str]
    learning_style: str
    engagement_metrics: Dict[str, float]


class AILearningAssistant:
    """AI-powered learning assistant that provides personalized education."""

    def __init__(self) -> None:
        """Initialize the learning assistant."""
        # Load environment variables
        load_dotenv()
        
        # Initialize RAG provider
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
            
        self.rag_provider = SupabaseRAGProvider(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
        )
        
        self.group_id: str = ""  # Will be set in initialize()
        self.current_progress: Optional[LearningProgress] = None
        self.output_dir = Path("examples/output/learning_assistant")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """Initialize the assistant and its components."""
        await self.rag_provider.initialize()
        
        # Define learning tools
        tools = [
            {
                "name": "assess_knowledge",
                "description": "Assess student's current knowledge level",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "responses": {"type": "object"},
                    },
                    "required": ["topic", "responses"],
                },
            },
            {
                "name": "generate_lesson",
                "description": "Generate a personalized lesson",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "level": {"type": "integer"},
                        "style": {"type": "string"},
                    },
                    "required": ["topic", "level", "style"],
                },
            },
            {
                "name": "create_quiz",
                "description": "Create an assessment quiz",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "difficulty": {"type": "string"},
                    },
                    "required": ["topic", "difficulty"],
                },
            },
            {
                "name": "search_resources",
                "description": "Search for educational resources",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "type": {"type": "string"},
                    },
                    "required": ["query"],
                },
            },
        ]

        # Configure LLM
        llm_config = {
            "config_list": [{
                "model": "anthropic/claude-3-opus-20240229",
                "api_key": os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY", ""),
                "base_url": "https://openrouter.ai/api/v1",
                "api_type": "openai",
            }],
            "temperature": 0.7,
            "functions": tools,
        }

        # Create specialized learning agents
        self.group_id = await create_agent_group(
            agents=[
                {
                    "type": "user",
                    "name": "student",
                    "system_message": "",
                    "config": {},
                },
                {
                    "type": "assistant",
                    "name": "tutor",
                    "system_message": (
                        "You are an expert tutor specialized in:\n"
                        "1. Assessing student knowledge and learning style\n"
                        "2. Creating personalized learning plans\n"
                        "3. Providing clear explanations and examples\n"
                        "4. Offering constructive feedback and encouragement\n"
                    ),
                    "config": {},
                },
                {
                    "type": "assistant",
                    "name": "content_creator",
                    "system_message": (
                        "You are an educational content creator focused on:\n"
                        "1. Creating engaging learning materials\n"
                        "2. Developing interactive exercises\n"
                        "3. Designing effective assessments\n"
                        "4. Incorporating multimedia elements\n"
                    ),
                    "config": {},
                },
                {
                    "type": "assistant",
                    "name": "learning_analyst",
                    "system_message": (
                        "You are a learning analytics expert specialized in:\n"
                        "1. Tracking learning progress\n"
                        "2. Identifying knowledge gaps\n"
                        "3. Recommending learning strategies\n"
                        "4. Measuring learning effectiveness\n"
                    ),
                    "config": {},
                },
            ],
            name="Learning Assistant Team",
            description="A team of AI experts that provide personalized education",
            use_group_chat=True,
            llm_config=llm_config,
        )

    async def start_learning_session(
        self,
        student_id: str,
        topic: str,
        initial_assessment: bool = True,
    ) -> LearningProgress:
        """Start a new learning session for a student.
        
        Args:
            student_id: Unique identifier for the student
            topic: The topic to learn
            initial_assessment: Whether to perform initial assessment
            
        Returns:
            The student's learning progress
        """
        print(f"\nStarting learning session for student {student_id} on topic: {topic}")
        
        # Create initial progress
        self.current_progress = LearningProgress(
            student_id=student_id,
            topic=topic,
            start_date=datetime.now(),
            current_level=0,
            completed_lessons=[],
            quiz_scores={},
            strengths=[],
            areas_for_improvement=[],
            learning_style="unknown",
            engagement_metrics={
                "participation": 0.0,
                "completion_rate": 0.0,
                "avg_quiz_score": 0.0,
            },
        )
        
        if initial_assessment:
            print("\nPerforming initial assessment...")
            await self._perform_assessment()
        
        # Index progress in RAG
        await self._index_progress()
        
        return self.current_progress

    async def get_next_lesson(self) -> Dict[str, Any]:
        """Get the next personalized lesson for the student.
        
        Returns:
            Lesson content and materials
            
        Raises:
            ValueError: If no learning session is active
        """
        if not self.current_progress:
            raise ValueError("No active learning session")
            
        print("\nGenerating next lesson...")
        
        # Get personalized lesson
        messages = await execute_task(
            group_id=self.group_id,
            task=(
                f"Generate a lesson for topic '{self.current_progress.topic}' "
                f"at level {self.current_progress.current_level} "
                f"optimized for {self.current_progress.learning_style} learning style"
            ),
        )
        
        # Parse lesson content
        lesson = {
            "title": "",
            "content": "",
            "exercises": [],
            "resources": [],
        }
        
        current_section = None
        for msg in messages:
            if "# " in msg.content:
                lesson["title"] = msg.content.split("# ")[1].strip()
            elif "## Exercises" in msg.content:
                current_section = "exercises"
            elif "## Resources" in msg.content:
                current_section = "resources"
            else:
                if current_section == "exercises":
                    lesson["exercises"].append(msg.content)
                elif current_section == "resources":
                    lesson["resources"].append(msg.content)
                else:
                    lesson["content"] += msg.content + "\n"
        
        # Generate audio version if appropriate
        if self.current_progress.learning_style == "auditory":
            print("\nGenerating audio version of lesson...")
            try:
                audio_data = await convert_text(
                    lesson["content"],
                    voice_id="en-US-neural2-J",  # Professional male voice
                    output_format="mp3",
                )
                
                audio_path = self.output_dir / f"lesson_{len(self.current_progress.completed_lessons) + 1}.mp3"
                save_audio(audio_data, str(audio_path))
                lesson["audio_path"] = str(audio_path)
            except Exception as e:
                print(f"Error generating audio: {e}")
        
        # Update progress
        self.current_progress.completed_lessons.append(lesson["title"])
        await self._index_progress()
        
        return lesson

    async def take_quiz(self, responses: Dict[str, str]) -> Dict[str, Any]:
        """Submit quiz responses and get feedback.
        
        Args:
            responses: Dictionary of question IDs to answers
            
        Returns:
            Quiz results and feedback
            
        Raises:
            ValueError: If no learning session is active
        """
        if not self.current_progress:
            raise ValueError("No active learning session")
            
        print("\nEvaluating quiz responses...")
        
        # Get quiz evaluation
        messages = await execute_task(
            group_id=self.group_id,
            task=f"Evaluate quiz responses for topic '{self.current_progress.topic}':\n{json.dumps(responses, indent=2)}",
        )
        
        # Parse results
        results = {
            "score": 0.0,
            "correct_answers": {},
            "explanations": {},
            "recommendations": [],
        }
        
        current_section = None
        for msg in messages:
            if "Score:" in msg.content:
                results["score"] = float(msg.content.split("Score:")[1].strip().rstrip("%")) / 100
            elif "## Correct Answers" in msg.content:
                current_section = "answers"
            elif "## Explanations" in msg.content:
                current_section = "explanations"
            elif "## Recommendations" in msg.content:
                current_section = "recommendations"
            else:
                if current_section == "answers":
                    # Parse answer line (e.g., "Q1: A")
                    parts = msg.content.split(":")
                    if len(parts) == 2:
                        results["correct_answers"][parts[0].strip()] = parts[1].strip()
                elif current_section == "explanations":
                    # Parse explanation line (e.g., "Q1: The reason is...")
                    parts = msg.content.split(":")
                    if len(parts) == 2:
                        results["explanations"][parts[0].strip()] = parts[1].strip()
                elif current_section == "recommendations":
                    results["recommendations"].append(msg.content)
        
        # Update progress
        quiz_id = f"quiz_{len(self.current_progress.quiz_scores) + 1}"
        self.current_progress.quiz_scores[quiz_id] = results["score"]
        self.current_progress.engagement_metrics["avg_quiz_score"] = (
            sum(self.current_progress.quiz_scores.values()) /
            len(self.current_progress.quiz_scores)
        )
        
        # Update areas for improvement based on quiz performance
        if results["score"] < 0.7:  # Below 70%
            self.current_progress.areas_for_improvement.extend(results["recommendations"])
            self.current_progress.areas_for_improvement = list(set(self.current_progress.areas_for_improvement))
        
        await self._index_progress()
        
        return results

    async def get_progress_report(self) -> Dict[str, Any]:
        """Get a detailed report of the student's learning progress.
        
        Returns:
            Progress report with metrics and recommendations
            
        Raises:
            ValueError: If no learning session is active
        """
        if not self.current_progress:
            raise ValueError("No active learning session")
            
        print("\nGenerating progress report...")
        
        # Get progress analysis
        messages = await execute_task(
            group_id=self.group_id,
            task=f"Analyze learning progress for student {self.current_progress.student_id}",
        )
        
        # Combine messages into report sections
        report = {
            "summary": "",
            "metrics": {
                "lessons_completed": len(self.current_progress.completed_lessons),
                "current_level": self.current_progress.current_level,
                "avg_quiz_score": self.current_progress.engagement_metrics["avg_quiz_score"],
                "engagement_rate": self.current_progress.engagement_metrics["participation"],
            },
            "strengths": self.current_progress.strengths,
            "areas_for_improvement": self.current_progress.areas_for_improvement,
            "recommendations": [],
        }
        
        current_section = None
        for msg in messages:
            if "## Summary" in msg.content:
                current_section = "summary"
            elif "## Recommendations" in msg.content:
                current_section = "recommendations"
            else:
                if current_section == "summary":
                    report["summary"] += msg.content + "\n"
                elif current_section == "recommendations":
                    report["recommendations"].append(msg.content)
        
        return report

    async def _perform_assessment(self) -> None:
        """Perform initial assessment of student's knowledge and learning style."""
        if not self.current_progress:
            return
            
        print("\nAssessing knowledge level and learning style...")
        
        # Get assessment
        messages = await execute_task(
            group_id=self.group_id,
            task=f"Assess initial knowledge and learning style for topic '{self.current_progress.topic}'",
        )
        
        # Parse assessment results
        for msg in messages:
            if "Learning Style:" in msg.content:
                self.current_progress.learning_style = msg.content.split("Learning Style:")[1].strip()
            elif "Initial Level:" in msg.content:
                try:
                    self.current_progress.current_level = int(msg.content.split("Initial Level:")[1].strip())
                except ValueError:
                    pass
            elif "Strengths:" in msg.content:
                strengths = msg.content.split("Strengths:")[1].strip().split("\n")
                self.current_progress.strengths.extend(s.strip("- ") for s in strengths if s.strip())
            elif "Areas for Improvement:" in msg.content:
                areas = msg.content.split("Areas for Improvement:")[1].strip().split("\n")
                self.current_progress.areas_for_improvement.extend(a.strip("- ") for a in areas if a.strip())

    async def _index_progress(self) -> None:
        """Index the current learning progress in RAG."""
        if not self.current_progress:
            return
            
        # Create progress document
        doc = Document(
            id=f"progress:{self.current_progress.student_id}:{self.current_progress.topic}",
            content=json.dumps(self.current_progress.__dict__),
            metadata={
                "type": "learning_progress",
                "student_id": self.current_progress.student_id,
                "topic": self.current_progress.topic,
            },
        )
        
        # Add to RAG provider
        await self.rag_provider.add_documents([doc])

    async def shutdown(self) -> None:
        """Clean up resources."""
        if self.group_id:
            await cleanup_group(self.group_id)
        await self.rag_provider.shutdown()


async def main() -> None:
    """Run the AI learning assistant example."""
    # Create and initialize assistant
    assistant = AILearningAssistant()
    await assistant.initialize()
    
    try:
        # Start learning session
        progress = await assistant.start_learning_session(
            student_id="student123",
            topic="Python Programming",
            initial_assessment=True,
        )
        
        print(f"\nInitial Assessment:")
        print(f"Learning Style: {progress.learning_style}")
        print(f"Current Level: {progress.current_level}")
        print(f"Strengths: {', '.join(progress.strengths)}")
        print(f"Areas for Improvement: {', '.join(progress.areas_for_improvement)}")
        
        # Get first lesson
        lesson = await assistant.get_next_lesson()
        print(f"\nFirst Lesson: {lesson['title']}")
        print(f"Content Preview: {lesson['content'][:200]}...")
        print(f"Number of Exercises: {len(lesson['exercises'])}")
        
        # Simulate taking a quiz
        quiz_responses = {
            "Q1": "Python is an interpreted, high-level programming language.",
            "Q2": "Lists, tuples, and dictionaries",
            "Q3": "def function_name(parameters):",
        }
        
        results = await assistant.take_quiz(quiz_responses)
        print(f"\nQuiz Results:")
        print(f"Score: {results['score'] * 100}%")
        print(f"Recommendations: {', '.join(results['recommendations'])}")
        
        # Get progress report
        report = await assistant.get_progress_report()
        print(f"\nProgress Report Summary:")
        print(report["summary"])
        print(f"Completed Lessons: {report['metrics']['lessons_completed']}")
        print(f"Average Quiz Score: {report['metrics']['avg_quiz_score'] * 100}%")
        print(f"Recommendations: {', '.join(report['recommendations'])}")
    
    finally:
        await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(main()) 