"""Story generation agent that creates consistent narratives."""

import json
import re
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, ValidationError

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.llms.base_llm import BaseLLM


class StoryScene(BaseModel):
    """A scene in the story."""

    title: str
    description: str
    characters: List[str]
    setting: str
    mood: str
    action: str
    image_prompt: str


class Story(BaseModel):
    """A complete story with scenes."""

    title: str
    description: str
    characters: Dict[str, str]  # name -> description
    scenes: List[StoryScene] = []


class StoryAgentConfig(BaseModel):
    """Configuration for story agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm: BaseLLM
    num_scenes: int = 5
    style: str = "fantasy"
    tone: str = "whimsical"


class StoryGenerationError(Exception):
    """Error during story generation."""

    pass


class StoryAgent(BaseAgent):
    """Agent that generates consistent stories with scenes."""

    def __init__(self, config: StoryAgentConfig) -> None:
        """Initialize story agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config

    @classmethod
    def validate_config(cls, config: Any) -> bool:
        """Validate agent configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        return (
            isinstance(config, StoryAgentConfig)
            and isinstance(config.llm, BaseLLM)
        )

    async def initialize(self) -> None:
        """Initialize the agent."""
        await self.config.llm.initialize()

    def extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text that may include markdown formatting.
        
        Args:
            text: Text that may contain JSON
            
        Returns:
            Extracted JSON object
            
        Raises:
            StoryGenerationError: If JSON cannot be parsed
        """
        try:
            # Try to extract JSON from markdown code block
            match = re.search(r"```(?:json)?\n(.*?)\n```", text, re.DOTALL)
            if match:
                text = match.group(1)
                
            # Clean up any remaining whitespace/newlines
            text = text.strip()
            
            return json.loads(text)
            
        except json.JSONDecodeError as e:
            # Try to find anything that looks like a JSON object
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
                    
            raise StoryGenerationError(
                f"Failed to parse JSON response: {str(e)}\n\nResponse text:\n{text}"
            ) from e

    async def generate_story_outline(self) -> Story:
        """Generate the main story outline.
        
        Returns:
            Story outline with title, description, and characters
            
        Raises:
            StoryGenerationError: If story generation fails
        """
        prompt = (
            f"Create a {self.config.style} story with a {self.config.tone} tone. "
            "Include a title, brief description, and 2-4 main characters with descriptions. "
            "Format the response as JSON with the following structure:\n"
            "{\n"
            '  "title": "Story title",\n'
            '  "description": "Story description",\n'
            '  "characters": {\n'
            '    "character_name": "character description",\n'
            '    ...\n'
            "  }\n"
            "}"
        )
        
        try:
            response = await self.config.llm.generate(prompt)
            data = self.extract_json(response.text)
            return Story(**data)
            
        except ValidationError as e:
            raise StoryGenerationError(
                f"Invalid story outline format: {str(e)}\n\nData:\n{data}"
            ) from e

    async def generate_scene(
        self,
        story: Story,
        scene_number: int,
        previous_scene: Optional[StoryScene] = None
    ) -> StoryScene:
        """Generate a single scene.
        
        Args:
            story: Story outline
            scene_number: Current scene number
            previous_scene: Previous scene for continuity
            
        Returns:
            Generated scene
            
        Raises:
            StoryGenerationError: If scene generation fails
        """
        prompt = (
            f"Create scene {scene_number} for the story '{story.title}'.\n\n"
            f"Story Description: {story.description}\n\n"
            "Characters:\n"
        )
        
        for name, desc in story.characters.items():
            prompt += f"- {name}: {desc}\n"
            
        if previous_scene:
            prompt += f"\nPrevious Scene:\n{previous_scene.description}\n"
            
        prompt += (
            "\nCreate a scene that advances the story. Include:\n"
            "1. A scene title\n"
            "2. Description of what happens\n"
            "3. Which characters are present\n"
            "4. The setting\n"
            "5. The mood/atmosphere\n"
            "6. The main action\n"
            "7. A detailed image prompt that captures the scene\n\n"
            "Format the response as JSON with the following structure:\n"
            "{\n"
            '  "title": "Scene title",\n'
            '  "description": "Scene description",\n'
            '  "characters": ["Character 1", "Character 2"],\n'
            '  "setting": "Scene setting",\n'
            '  "mood": "Scene mood",\n'
            '  "action": "Main action",\n'
            '  "image_prompt": "Detailed prompt for image generation"\n'
            "}"
        )
        
        try:
            response = await self.config.llm.generate(prompt)
            data = self.extract_json(response.text)
            return StoryScene(**data)
            
        except ValidationError as e:
            raise StoryGenerationError(
                f"Invalid scene format: {str(e)}\n\nData:\n{data}"
            ) from e

    async def process(self, input_text: str) -> Story:
        """Process input and generate story.
        
        Args:
            input_text: Optional theme or prompt for the story
            
        Returns:
            Generated story with scenes
            
        Raises:
            StoryGenerationError: If story generation fails
        """
        # Generate story outline
        story = await self.generate_story_outline()
        scenes = []
        previous_scene = None
        
        # Generate each scene
        for i in range(self.config.num_scenes):
            scene = await self.generate_scene(story, i + 1, previous_scene)
            scenes.append(scene)
            previous_scene = scene
            
        story.scenes = scenes
        return story

    async def process_stream(self, input_text: str) -> AsyncIterator[str]:
        """Process input and generate streaming response.
        
        Args:
            input_text: Optional theme or prompt for the story
            
        Returns:
            Story generation progress
        """
        try:
            # Generate story outline
            story = await self.generate_story_outline()
            yield f"Created story outline: {story.title}\n"
            
            scenes = []
            previous_scene = None
            
            # Generate each scene
            for i in range(self.config.num_scenes):
                scene = await self.generate_scene(story, i + 1, previous_scene)
                scenes.append(scene)
                previous_scene = scene
                yield f"Generated scene {i + 1}: {scene.title}\n"
                
            story.scenes = scenes
            yield "Story complete!"
            
        except StoryGenerationError as e:
            yield f"Error generating story: {str(e)}"

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.config.llm.cleanup() 