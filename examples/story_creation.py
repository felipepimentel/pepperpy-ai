"""Story creation example using Pepperpy.

Purpose:
    Demonstrate how to use Pepperpy for creating interactive children's stories
    using multiple specialized agents.

Requirements:
    - Python 3.9+
    - Pepperpy library
    - OpenAI API key

Usage:
    1. Install dependencies:
       pip install -r requirements.txt

    2. Set environment variables:
       export OPENAI_API_KEY=your_key_here

    3. Run the example:
       python story_creation.py
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from pepperpy.core.config import Configuration
from pepperpy.llm import BaseLLMProvider
from pepperpy.memory import BaseMemoryProvider
from pepperpy.synthesis import BaseSynthesisProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StoryCreator:
    """Creates interactive children's stories using multiple agents."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the story creator.

        Args:
            config_path: Optional path to configuration file
        """
        self.config = Configuration(config_path)
        self.output_dir = Path.home() / ".pepperpy" / "stories"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load providers
        self.llm_provider = self.config.load_provider("llm", "default", BaseLLMProvider)
        self.synthesis_provider = self.config.load_provider(
            "synthesis", "default", BaseSynthesisProvider
        )
        self.memory_provider = self.config.load_provider(
            "memory", "default", BaseMemoryProvider
        )

        # Setup agents
        self.agents = self._setup_agents()

    def _setup_agents(self) -> Dict[str, Dict[str, Any]]:
        """Set up specialized agents for story creation.

        Returns:
            Dictionary of agent configurations
        """
        return {
            "child_expert": {
                "role": "Child Development Expert",
                "expertise": [
                    "child psychology",
                    "education",
                    "age-appropriate content",
                ],
                "tools": [self.llm_provider],
            },
            "storyteller": {
                "role": "Creative Storyteller",
                "expertise": ["narrative", "creativity", "engagement"],
                "tools": [self.llm_provider],
            },
            "character_designer": {
                "role": "Character Designer",
                "expertise": ["character development", "dialogue", "personality"],
                "tools": [self.llm_provider],
            },
            "critic": {
                "role": "Content Reviewer",
                "expertise": [
                    "content appropriateness",
                    "educational value",
                    "engagement",
                ],
                "tools": [self.llm_provider],
            },
        }

    async def create_story(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a children's story based on parameters.

        Args:
            params: Story parameters including:
                - age_range: Target age range (e.g., "6-8")
                - theme: Story theme (e.g., "friendship")
                - duration: Approximate duration (e.g., "10min")
                - elements: Story elements (characters, setting, etc.)
                - preferences: Style preferences

        Returns:
            Dictionary containing:
                - audio_path: Path to generated audio file
                - transcript: Story text
                - metadata: Story metadata
        """
        logger.info("Creating story with parameters: %s", params)

        # Get expert input
        expert_prompt = self._create_expert_prompt(params)
        expert_input = await self.llm_provider.generate(expert_prompt)

        # Generate story outline
        outline_prompt = self._create_outline_prompt(expert_input, params)
        story_outline = await self.llm_provider.generate(outline_prompt)

        # Design characters
        character_prompt = self._create_character_prompt(story_outline, params)
        characters = await self.llm_provider.generate(character_prompt)

        # Write story
        story_prompt = self._create_story_prompt(
            story_outline, characters, expert_input, params
        )
        story = await self.llm_provider.generate(story_prompt)

        # Review content
        review_prompt = self._create_review_prompt(story, params)
        review = await self.llm_provider.generate(review_prompt)

        # Revise if needed
        if self._needs_revision(review):
            revision_prompt = self._create_revision_prompt(story, review, params)
            story = await self.llm_provider.generate(revision_prompt)

        # Generate audio
        audio_data = await self.synthesis_provider.synthesize(
            story, language=params.get("language", "pt-BR")
        )

        # Save audio
        output_path = self.output_dir / f"story_{asyncio.get_event_loop().time()}.mp3"
        audio_path = await self.synthesis_provider.save(audio_data, output_path)

        # Store in memory
        await self.memory_provider.set(
            f"story_{audio_path.stem}",
            {
                "text": story,
                "parameters": params,
                "review": review,
                "audio_path": str(audio_path),
            },
        )

        return {
            "audio_path": audio_path,
            "transcript": story,
            "metadata": {
                "age_range": params["age_range"],
                "theme": params["theme"],
                "duration": params["duration"],
                "review": review,
            },
        }

    def _create_expert_prompt(self, params: Dict[str, Any]) -> str:
        """Create prompt for child development expert."""
        return f"""As a child development expert, provide guidelines for a story with:
- Target age: {params["age_range"]}
- Theme: {params["theme"]}
- Duration: {params["duration"]}

Consider:
1. Age-appropriate vocabulary and concepts
2. Educational value
3. Emotional development
4. Attention span
5. Learning opportunities

Provide specific recommendations for:
1. Language complexity
2. Story structure
3. Character types
4. Moral lessons
5. Interactive elements"""

    def _create_outline_prompt(self, expert_input: str, params: Dict[str, Any]) -> str:
        """Create prompt for story outline."""
        return f"""Create a story outline following these expert guidelines:
{expert_input}

Story parameters:
- Theme: {params["theme"]}
- Setting: {params["elements"].get("setting", "Not specified")}
- Number of characters: {params["elements"].get("characters", 2)}
- Moral: {params["elements"].get("moral", "Not specified")}

Create a detailed outline with:
1. Beginning - Setup and character introduction
2. Middle - Conflict and challenges
3. End - Resolution and moral lesson
4. Key story beats
5. Interactive moments"""

    def _create_character_prompt(self, outline: str, params: Dict[str, Any]) -> str:
        """Create prompt for character design."""
        return f"""Design characters for this story outline:
{outline}

Requirements:
- Age-appropriate for {params["age_range"]}
- Relatable personalities
- Clear roles in the story
- Distinct voices and traits
- Educational value

For each character, provide:
1. Name and description
2. Personality traits
3. Role in the story
4. Speech patterns
5. Growth arc"""

    def _create_story_prompt(
        self, outline: str, characters: str, expert_input: str, params: Dict[str, Any]
    ) -> str:
        """Create prompt for story writing."""
        return f"""Write a children's story using:

Expert guidelines:
{expert_input}

Outline:
{outline}

Characters:
{characters}

Requirements:
- Duration: {params["duration"]}
- Style: {params["preferences"].get("style", "adventure")}
- Complexity: {params["preferences"].get("complexity", "moderate")}
- Language: {params["preferences"].get("language", "pt-BR")}

Create an engaging story with:
1. Clear narrative flow
2. Age-appropriate language
3. Educational elements
4. Interactive moments
5. Moral lessons"""

    def _create_review_prompt(self, story: str, params: Dict[str, Any]) -> str:
        """Create prompt for content review."""
        return f"""Review this children's story for:

Story:
{story}

Evaluate:
1. Age-appropriateness for {params["age_range"]}
2. Educational value
3. Engagement level
4. Content safety
5. Language suitability
6. Moral clarity
7. Entertainment value

Provide:
1. Overall assessment
2. Specific concerns
3. Improvement suggestions
4. Rating for each aspect (1-5)"""

    def _create_revision_prompt(
        self, story: str, review: str, params: Dict[str, Any]
    ) -> str:
        """Create prompt for story revision."""
        return f"""Revise this story based on the review:

Original story:
{story}

Review feedback:
{review}

Requirements:
1. Address all concerns
2. Maintain age-appropriateness for {params["age_range"]}
3. Keep core narrative
4. Enhance educational value
5. Improve engagement

Provide the revised story with all improvements implemented."""

    def _needs_revision(self, review: str) -> bool:
        """Check if story needs revision based on review."""
        # Simple check for now - could be more sophisticated
        return "concern" in review.lower() or "improve" in review.lower()

    async def generate(self) -> Dict[str, Any]:
        """Generate a story with default parameters.

        Returns:
            Story result including audio path and metadata
        """
        default_params = {
            "age_range": "6-8",
            "theme": "friendship and cooperation",
            "duration": "10min",
            "elements": {
                "characters": 2,
                "moral": "working together",
                "setting": "magical forest",
            },
            "preferences": {
                "style": "light adventure",
                "complexity": "moderate",
                "language": "pt-BR",
            },
        }
        return await self.create_story(default_params)


async def main():
    """Run the example."""
    creator = StoryCreator()
    result = await creator.generate()
    logger.info("Generated story: %s", result["audio_path"])
    logger.info("Story metadata: %s", result["metadata"])


if __name__ == "__main__":
    asyncio.run(main())
