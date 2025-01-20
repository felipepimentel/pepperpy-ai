"""Art generation agent that creates consistent visuals."""

import json
import os
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.agents.story_agent import Story, StoryScene
from pepperpy.llms.base_llm import BaseLLM
from pepperpy.tools.functions.stability import StabilityTool


class CharacterStyle(BaseModel):
    """Visual style for a character."""

    name: str
    appearance: str
    style_prompt: str
    negative_prompt: Optional[str] = None


class ArtAgentConfig(BaseModel):
    """Configuration for art agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm: BaseLLM
    stability_tool: StabilityTool
    style_preset: Optional[str] = None
    output_dir: str = "story_images"


class ArtAgent(BaseAgent):
    """Agent that generates consistent artwork for stories."""

    def __init__(self, config: ArtAgentConfig) -> None:
        """Initialize art agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.character_styles: Dict[str, CharacterStyle] = {}

    @classmethod
    def validate_config(cls, config: Any) -> bool:
        """Validate agent configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        return (
            isinstance(config, ArtAgentConfig)
            and isinstance(config.llm, BaseLLM)
            and isinstance(config.stability_tool, StabilityTool)
        )

    async def initialize(self) -> None:
        """Initialize the agent."""
        await self.config.llm.initialize()
        await self.config.stability_tool.initialize()

    async def generate_character_styles(self, story: Story) -> None:
        """Generate consistent visual styles for characters.
        
        Args:
            story: Story with characters to style
        """
        for name, description in story.characters.items():
            # Generate appearance description
            appearance_prompt = (
                f"Create a detailed visual description for the character '{name}' "
                f"based on this description: {description}\n\n"
                "Focus on physical appearance, clothing, and distinguishing features. "
                "Keep the description clear and specific, suitable for image generation."
            )
            appearance_response = await self.config.llm.generate(appearance_prompt)
            appearance = appearance_response.text.strip()

            # Generate style prompt
            style_prompt_request = (
                f"Based on this character description:\n{appearance}\n\n"
                "Create a concise style prompt for image generation. "
                "Focus on key visual elements, artistic style, and important details. "
                "Keep it clear and specific."
            )
            style_response = await self.config.llm.generate(style_prompt_request)
            style_prompt = style_response.text.strip()

            # Generate negative prompt
            negative_prompt_request = (
                f"For this character:\n{appearance}\n\n"
                "Create a negative prompt for image generation - "
                "list specific elements to avoid to maintain character consistency. "
                "Focus on what should NOT appear in the generated images."
            )
            negative_response = await self.config.llm.generate(negative_prompt_request)
            negative_prompt = negative_response.text.strip()

            # Create character style
            self.character_styles[name] = CharacterStyle(
                name=name,
                appearance=appearance,
                style_prompt=style_prompt,
                negative_prompt=negative_prompt
            )

    async def enhance_image_prompt(self, scene: StoryScene) -> str:
        """Enhance scene's image prompt with character styles.
        
        Args:
            scene: Scene to generate image for
            
        Returns:
            Enhanced image prompt
        """
        # Start with the scene's core image prompt
        prompt = scene.image_prompt
        
        # Add key character details
        for character in scene.characters:
            if character in self.character_styles:
                style = self.character_styles[character]
                # Add only the most important visual elements
                key_elements = await self.config.llm.generate(
                    f"Extract 2-3 key visual elements from this style prompt, separated by commas:\n{style.style_prompt}"
                )
                prompt += f", {key_elements.text.strip()}"
                
        # Add scene mood and setting
        prompt += f", {scene.mood}, {scene.setting}"
        
        # Add quality keywords
        prompt += ", highly detailed, professional quality, masterpiece"
        
        # Ensure prompt is not too long
        if len(prompt) > 1500:  # Leave some buffer for safety
            prompt = prompt[:1500]
            
        return prompt

    async def get_negative_prompt(self, scene: StoryScene) -> str:
        """Get combined negative prompt for scene.
        
        Args:
            scene: Scene to generate image for
            
        Returns:
            Combined negative prompt
        """
        negative_parts = [
            "low quality, blurry, distorted, deformed",
            "amateur, poorly drawn, bad anatomy",
        ]
        
        # Add only the most important negative elements from characters
        for character in scene.characters:
            if character in self.character_styles:
                style = self.character_styles[character]
                if style.negative_prompt:
                    # Extract key negative elements
                    key_negatives = await self.config.llm.generate(
                        f"Extract 2-3 key elements to avoid from this negative prompt, separated by commas:\n{style.negative_prompt}"
                    )
                    negative_parts.append(key_negatives.text.strip())
                    
        # Combine and ensure not too long
        negative_prompt = ", ".join(negative_parts)
        if len(negative_prompt) > 1500:  # Leave some buffer for safety
            negative_prompt = negative_prompt[:1500]
            
        return negative_prompt

    async def generate_scene_image(
        self,
        scene: StoryScene,
        scene_number: int
    ) -> List[str]:
        """Generate image for a scene.
        
        Args:
            scene: Scene to generate image for
            scene_number: Scene number for file naming
            
        Returns:
            Paths to generated images
            
        Raises:
            Exception: If image generation fails or returns no data
        """
        # Create scene-specific output directory
        output_dir = os.path.join(self.config.output_dir, f"scene_{scene_number}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate image
        result = await self.config.stability_tool.execute(
            prompt=await self.enhance_image_prompt(scene),
            negative_prompt=await self.get_negative_prompt(scene),
            style_preset=self.config.style_preset,
            output_dir=output_dir,
        )
        
        if not result.success or not result.data:
            raise Exception(f"Failed to generate image: {result.error}")
            
        return result.data.image_paths

    async def process(self, story: Story) -> Dict[int, List[str]]:
        """Process story and generate images.
        
        Args:
            story: Story to generate images for
            
        Returns:
            Dictionary mapping scene numbers to image paths
        """
        # Generate character styles first
        await self.generate_character_styles(story)
        
        # Generate images for each scene
        scene_images = {}
        for i, scene in enumerate(story.scenes):
            image_paths = await self.generate_scene_image(scene, i + 1)
            scene_images[i + 1] = image_paths
            
        return scene_images

    async def process_stream(self, story: Story) -> AsyncIterator[str]:
        """Process story and generate images with progress updates.
        
        Args:
            story: Story to generate images for
            
        Returns:
            Progress updates
        """
        yield "Generating character styles...\n"
        await self.generate_character_styles(story)
        
        for i, scene in enumerate(story.scenes):
            scene_num = i + 1
            yield f"Generating image for scene {scene_num}: {scene.title}\n"
            
            try:
                image_paths = await self.generate_scene_image(scene, scene_num)
                yield f"Created {len(image_paths)} images for scene {scene_num}\n"
            except Exception as e:
                yield f"Error generating image for scene {scene_num}: {str(e)}\n"
                
        yield "Image generation complete!"

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.config.llm.cleanup()
        await self.config.stability_tool.cleanup() 