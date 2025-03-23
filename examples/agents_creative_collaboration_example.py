"""Example of a creative collaboration system using PepperPy agents.

This example demonstrates a creative team that combines:
1. Brainstorming and idea generation
2. Story development and narrative design
3. Visual concept creation
4. Project management and feedback
5. Content refinement and editing
"""

import asyncio
import os
from typing import AsyncGenerator, Dict, List, Optional, Union
import json
from datetime import datetime

from dotenv import load_dotenv

from pepperpy.agents import create_agent_group, execute_task, cleanup_group
from pepperpy.agents.provider import Message
from pepperpy.rag.providers.supabase import SupabaseRAGProvider


async def generate_ideas(prompt: str) -> str:
    """Generate creative ideas based on a prompt."""
    # Simulated idea generation
    ideas = {
        "story": """
        === Story Ideas ===
        
        1. "The Digital Oracle"
        Theme: AI and human intuition
        Premise: A programmer discovers an AI that can predict personal futures,
        but its predictions become self-fulfilling prophecies.
        
        2. "Memory Architects"
        Theme: Virtual reality and memory
        Premise: In a world where memories can be designed and implanted,
        a memory architect discovers a glitch in the system.
        
        3. "The Last Algorithm"
        Theme: Ethics in AI development
        Premise: An AI researcher creates an algorithm that can solve any problem,
        but must decide whether to share it with the world.
        """,
        "game": """
        === Game Concepts ===
        
        1. "Mind Maze"
        Genre: Puzzle/Adventure
        Concept: Players navigate through a maze that adapts to their thought
        patterns and emotional state.
        
        2. "Quantum Tales"
        Genre: RPG/Strategy
        Concept: Players manage parallel timelines, making decisions that
        affect multiple realities simultaneously.
        
        3. "Code Warriors"
        Genre: Action/Educational
        Concept: Players write real code to create abilities and solve
        challenges in a cyberpunk world.
        """,
        "app": """
        === App Ideas ===
        
        1. "MoodScape"
        Type: Wellness/Productivity
        Concept: An app that creates personalized environments (music, visuals,
        tasks) based on user's emotional state and goals.
        
        2. "LearnLoop"
        Type: Education
        Concept: Adaptive learning platform that uses AI to create personalized
        learning paths through interactive content.
        
        3. "CreativeFlow"
        Type: Creativity Tool
        Concept: AI-powered brainstorming tool that helps users explore and
        develop creative ideas through guided exercises.
        """
    }
    return ideas.get(prompt.lower(), f"No ideas generated for: {prompt}")


async def develop_concept(concept: str) -> str:
    """Develop and expand a creative concept."""
    # Simulated concept development
    return f"""
    === Concept Development ===
    
    Title: {concept}
    
    Expanded Outline:
    1. Core Elements
       - Central theme: Technology vs. Humanity
       - Target audience: Tech-savvy adults
       - Unique selling points: Interactive storytelling
    
    2. Structure
       - Beginning: Setup of the world and conflict
       - Middle: Exploration of consequences
       - End: Resolution and revelation
    
    3. Key Components
       - Character arcs
       - Plot points
       - World-building elements
    
    4. Technical Requirements
       - Platform considerations
       - Resource needs
       - Timeline estimates
    
    5. Next Steps
       - Detailed outline
       - Prototype development
       - User testing plan
    """


async def review_content(content: str) -> str:
    """Review and provide feedback on creative content."""
    # Simulated content review
    return """
    === Content Review ===
    
    Strengths:
    1. Strong central concept
    2. Clear narrative structure
    3. Engaging character development
    
    Areas for Improvement:
    1. Pacing in middle section
    2. Character motivations
    3. World-building details
    
    Technical Aspects:
    - Grammar and style: Excellent
    - Consistency: Good
    - Flow: Needs minor adjustments
    
    Recommendations:
    1. Expand character backstories
    2. Add more sensory details
    3. Strengthen transitions
    """


async def print_stream(stream: Union[List[Message], AsyncGenerator[Message, None]]) -> None:
    """Print messages or stream with appropriate formatting."""
    if isinstance(stream, list):
        for msg in stream:
            print(f"\n{msg.role}: {msg.content}\n")
            print("-" * 80)
    else:
        current_role = None
        async for msg in stream:
            if msg.role != current_role:
                if current_role is not None:
                    print("\n" + "-" * 80)
                print(f"\n{msg.role}: ", end="", flush=True)
                current_role = msg.role
            print(msg.content, end="", flush=True)
        print("\n" + "-" * 80)


async def main() -> None:
    """Run the creative collaboration example."""
    # Load environment variables
    load_dotenv()

    # Initialize RAG system with Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
    
    rag_provider = SupabaseRAGProvider(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
    )

    # Define creative tools
    tools = [
        {
            "name": "generate_ideas",
            "description": "Generate creative ideas based on a prompt",
            "function": generate_ideas,
            "parameters": {
                "prompt": {
                    "type": "string",
                    "description": "The type of ideas to generate (e.g., 'story', 'game', 'app')",
                },
            },
        },
        {
            "name": "develop_concept",
            "description": "Develop and expand a creative concept",
            "function": develop_concept,
            "parameters": {
                "concept": {
                    "type": "string",
                    "description": "The concept to develop",
                },
            },
        },
        {
            "name": "review_content",
            "description": "Review and provide feedback on creative content",
            "function": review_content,
            "parameters": {
                "content": {
                    "type": "string",
                    "description": "The content to review",
                },
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
        "temperature": 0.8,  # Slightly higher temperature for more creative responses
    }

    # Create creative team
    group_id = await create_agent_group(
        agents=[
            {
                "type": "assistant",
                "name": "creative_director",
                "system_message": (
                    "You are a creative director with expertise in storytelling "
                    "and project management. Your role is to:\n"
                    "1. Guide the creative vision\n"
                    "2. Facilitate brainstorming\n"
                    "3. Evaluate and refine ideas\n"
                    "4. Ensure project coherence\n"
                    "\nUse the generate_ideas tool to spark creativity and the "
                    "develop_concept tool to expand promising ideas."
                ),
                "config": {
                    "tools": tools,
                    "memory": {
                        "type": "conversation",
                        "max_messages": 15,
                    },
                },
            },
            {
                "type": "assistant",
                "name": "story_architect",
                "system_message": (
                    "You are a narrative designer and storyteller. Your role is to:\n"
                    "1. Develop compelling narratives\n"
                    "2. Create engaging characters\n"
                    "3. Structure story elements\n"
                    "4. Maintain narrative consistency\n"
                    "\nUse the develop_concept tool to flesh out story elements "
                    "and the review_content tool to refine narratives."
                ),
                "config": {
                    "tools": tools,
                    "memory": {
                        "type": "conversation",
                        "max_messages": 15,
                    },
                },
            },
            {
                "type": "assistant",
                "name": "content_editor",
                "system_message": (
                    "You are an experienced content editor. Your role is to:\n"
                    "1. Review and refine content\n"
                    "2. Ensure quality and consistency\n"
                    "3. Provide constructive feedback\n"
                    "4. Polish final deliverables\n"
                    "\nUse the review_content tool to evaluate work and provide "
                    "specific improvement suggestions."
                ),
                "config": {
                    "tools": tools,
                    "memory": {
                        "type": "conversation",
                        "max_messages": 15,
                    },
                },
            },
            {
                "type": "user",
                "name": "creator",
                "system_message": (
                    "You are a creator working on an innovative project. "
                    "Feel free to share ideas, ask for feedback, and collaborate "
                    "with the team to develop your vision."
                ),
            },
        ],
        name="creative_team",
        description="A team for collaborative creative development",
        llm_config=llm_config,
        use_group_chat=True,
        max_rounds=15,
    )

    try:
        # Example 1: Brainstorming Session
        print("\n=== Brainstorming Session ===")
        messages = await execute_task(
            group_id=group_id,
            task=(
                "I want to create an innovative app that combines education and gaming. "
                "Could you help me:\n"
                "1. Generate initial ideas\n"
                "2. Explore different concepts\n"
                "3. Identify unique opportunities\n"
                "4. Select the most promising direction"
            ),
        )
        await print_stream(messages)

        # Example 2: Concept Development
        print("\n=== Concept Development Session ===")
        concept = "LearnLoop - An AI-powered educational game platform"
        messages = await execute_task(
            group_id=group_id,
            task=(
                f"Let's develop the concept for {concept}. Please help me:\n"
                "1. Define core features and mechanics\n"
                "2. Create a compelling narrative framework\n"
                "3. Plan the user experience\n"
                "4. Identify technical requirements"
            ),
        )
        await print_stream(messages)

        # Example 3: Content Review
        print("\n=== Content Review Session ===")
        content = """
        LearnLoop: Where Learning Meets Adventure

        In LearnLoop, students become Knowledge Explorers, embarking on
        personalized learning quests through interactive worlds. Each world
        represents a different subject area, with AI-driven challenges that
        adapt to the student's learning style and pace.

        Key Features:
        - Personalized learning paths
        - Interactive storytelling
        - Real-time feedback
        - Collaborative challenges
        - Progress visualization
        """
        messages = await execute_task(
            group_id=group_id,
            task=(
                "Could you review this initial content and help me:\n"
                "1. Evaluate the overall concept\n"
                "2. Identify areas for improvement\n"
                "3. Suggest specific enhancements\n"
                "4. Refine the messaging"
            ),
        )
        await print_stream(messages)

    finally:
        # Clean up
        await cleanup_group(group_id)
        await rag_provider.shutdown()


if __name__ == "__main__":
    asyncio.run(main()) 