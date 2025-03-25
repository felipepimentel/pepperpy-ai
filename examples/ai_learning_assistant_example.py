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

try:
    from dotenv import load_dotenv
except ImportError:
    # Mock load_dotenv if not available
    def load_dotenv():
        """Mock function for load_dotenv."""
        print("Warning: dotenv not available, skipping environment loading")

from pepperpy.rag import Document
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
        
        # Dummy Supabase values for example purposes
        self.rag_provider = None
        # Skip RAG provider initialization for this example
        print("Note: This example requires Supabase credentials. Using mock data instead.")
        
        self.group_id: str = "mock-group-id"  # Mock group ID for the example
        self.current_progress: Optional[LearningProgress] = None
        self.output_dir = Path("examples/output/learning_assistant")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """Initialize the assistant and its components."""
        print("Initializing AI Learning Assistant (simulation)...")
        # Skip actual initialization for this example
        
    async def load_student_data(self, student_id: str) -> Dict[str, Any]:
        """Load student data from file or create dummy data if file doesn't exist."""
        student_data_path = Path("examples/input/student_data.json")
        
        try:
            if student_data_path.exists():
                with open(student_data_path, "r") as f:
                    return json.load(f)
            else:
                print(f"Warning: Student data file not found at {student_data_path}")
                # Return dummy data
                return {
                    "student_id": student_id,
                    "name": "Example Student",
                    "age": 20,
                    "education_level": "undergraduate",
                    "learning_style": "visual",
                    "interests": ["machine learning", "programming"],
                    "previous_experience": {"python": "beginner"},
                    "goals": ["Learn programming basics"],
                    "preferred_learning_pace": "moderate",
                    "available_time_weekly": 10
                }
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {student_data_path}, using dummy data")
            # Return dummy data in case of JSON error
            return {
                "student_id": student_id,
                "name": "Example Student",
                "learning_style": "visual"
            }

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
        await self.add_to_knowledge_base(doc)

    async def add_to_knowledge_base(self, document: Document) -> None:
        """Add a document to the RAG knowledge base.
        
        Args:
            document: Document to add
        """
        if self.rag_provider:
            await self.rag_provider.add_documents([document])
        else:
            print("Mock: Adding document to knowledge base (simulation only)")

    async def shutdown(self) -> None:
        """Shutdown the assistant and clean up resources."""
        print("Shutting down AI Learning Assistant...")
        if self.rag_provider:
            await self.rag_provider.shutdown()
        print("Resources cleaned up successfully")


async def main() -> None:
    """Run the learning assistant example."""
    print("AI Learning Assistant Example")
    print("=" * 80)
    
    assistant = AILearningAssistant()
    await assistant.initialize()
    
    # Load student data
    student_data = await assistant.load_student_data("student123")
    print(f"\nLoaded student data for: {student_data.get('name', 'Unknown Student')}")
    print(f"Learning style: {student_data.get('learning_style', 'Unknown')}")
    print(f"Interests: {', '.join(student_data.get('interests', ['None']))}")
    
    print("\nThis is a demonstration example. In a real implementation:")
    print("1. The assistant would connect to Supabase for RAG capabilities")
    print("2. Multiple specialized agents would interact to provide learning")
    print("3. Generated lessons and quizzes would be created dynamically")
    print("4. Student progress would be tracked and used to personalize content")
    print("\nExample completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 