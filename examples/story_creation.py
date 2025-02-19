"""Story creation example using Pepperpy.

Purpose:
    Demonstrate how to create an automated story generator that:
    - Plans story structure and plot
    - Writes engaging narratives
    - Edits and refines content
    - Narrates the story with voice

    This example showcases agent orchestration and chain-based workflows:
    1. Agent Chain:
       - StoryPlanner: Outlines plot and structure
       - StoryWriter: Creates narrative content
       - StoryEditor: Refines and improves text
       - Narrator: Converts to audio

    2. Memory Integration:
       - Story state tracking
       - Version history
       - Context preservation

    3. LLM Coordination:
       - Role-specific prompting
       - Context sharing
       - Output validation

    4. Audio Generation:
       - Character-aware voices
       - Emotion-based effects
       - Scene transitions

Requirements:
    - Python 3.9+
    - Pepperpy library
    - OpenAI API key
    - Internet connection

Configuration:
    1. Environment Variables:
       - OPENAI_API_KEY (required)
         Description: OpenAI API key for LLM and TTS
         Example: export OPENAI_API_KEY=sk-...

       - PEPPERPY_OUTPUT_DIR (optional)
         Description: Custom output directory for stories
         Default: ~/.pepperpy/stories
         Example: export PEPPERPY_OUTPUT_DIR=/path/to/stories

    2. StoryGenerator Parameters:
       - output_dir: Optional[Path]
         Description: Custom output directory
         Default: ~/.pepperpy/stories

       - language: str
         Description: Story language
         Default: "en-US"

       - max_length: int
         Description: Maximum story length
         Default: 1000

Usage:
    1. Install dependencies:
       poetry install

    2. Set environment variables:
       export OPENAI_API_KEY=your_key_here

    3. Run the example:
       poetry run python examples/story_creation.py
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from pepperpy import Pepperpy
from pepperpy.agents.chains.base import Chain
from pepperpy.agents.manager import AgentManager
from pepperpy.core.base import BaseComponent
from pepperpy.core.errors import ConfigurationError

logger = logging.getLogger(__name__)


class StoryGenerator(BaseComponent):
    """Story generator using multi-agent coordination."""

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        language: str = "en-US",
        max_length: int = 1000,
    ) -> None:
        """Initialize story generator.

        Args:
            output_dir: Custom output directory
            language: Story language
            max_length: Maximum story length

        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__(id=uuid.uuid4())
        self.output_dir = output_dir or Path.home() / ".pepperpy" / "stories"
        self.language = language
        self.max_length = max_length
        self.pepper: Optional[Pepperpy] = None
        self.manager: Optional[AgentManager] = None

    async def initialize(self) -> None:
        """Initialize the generator.

        Raises:
            ConfigurationError: If initialization fails
        """
        try:
            # Initialize Pepperpy
            self.pepper = await Pepperpy.create()
            self.manager = AgentManager()

            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            logger.info("Initialized story generator")
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.manager:
            await self.manager.cleanup()

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.output_dir:
            raise ConfigurationError("Output directory not set")

    async def create_story(
        self,
        theme: Optional[str] = None,
        genre: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a story using multi-agent coordination.

        Args:
            theme: Optional story theme
            genre: Optional story genre

        Returns:
            Dictionary containing:
            - text: Generated story text
            - audio_path: Path to audio file
            - metadata: Story metadata

        Raises:
            Exception: If story creation fails
        """
        try:
            # Create agent chain
            chain = Chain(
                [
                    "story_planner",  # Plans plot and structure
                    "story_writer",  # Creates narrative
                    "story_editor",  # Refines content
                    "narrator",  # Converts to audio
                ]
            )

            # Set chain context
            context = {
                "theme": theme,
                "genre": genre,
                "language": self.language,
                "max_length": self.max_length,
                "output_dir": self.output_dir,
            }

            # Execute chain
            result = await chain.run(context=context)

            return {
                "text": result.story,
                "audio_path": result.audio_path,
                "metadata": result.metadata,
            }

        except Exception as e:
            logger.error("Failed to create story", exc_info=e)
            raise

    async def generate(
        self,
        theme: Optional[str] = None,
        genre: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a story with audio narration.

        Args:
            theme: Optional story theme
            genre: Optional story genre

        Returns:
            Dictionary containing:
            - text: Generated story text
            - audio_path: Path to audio file
            - metadata: Story metadata

        Raises:
            Exception: If generation fails
        """
        try:
            # Validate configuration
            self.validate()

            # Create story
            result = await self.create_story(theme, genre)

            logger.info(
                "Generated story",
                extra={
                    "theme": theme,
                    "genre": genre,
                    "audio_path": result["audio_path"],
                },
            )

            return result

        except Exception as e:
            logger.error("Failed to generate story", exc_info=e)
            raise


async def main() -> None:
    """Run the story creation example."""
    # Initialize generator
    generator = StoryGenerator()
    await generator.initialize()

    try:
        # Generate story
        result = await generator.generate(
            theme="adventure",
            genre="fantasy",
        )

        print(f"Generated story: {result['audio_path']}")
        print("\nStory text:")
        print(result["text"])

    finally:
        await generator.cleanup()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Run example
    asyncio.run(main())
